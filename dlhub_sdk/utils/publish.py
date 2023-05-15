import logging
import json
import requests

from funcx import ContainerSpec
from time import sleep
import github
from dlhub_sdk.config import GLOBUS_SEARCH_WRITER_LAMBDA
import base64

import mdf_toolbox

from zipfile import ZipFile


logger = logging.getLogger(__name__)


def create_container_spec(metadata):
    """
    Create the container spec for the Container Service. Iterate through
    the dependencies and add them. Also include parsl, toolbox, home_run, etc.

    :param metadata:
    :return:
    """

    # Get the list of requirements from the schema
    dependencies = []
    try:
        for k, v in metadata['dlhub']['dependencies']['python'].items():
            dependencies.append("{0}=={1}".format(k, v))
    except Exception:
        # There are no python dependencies
        pass

    # If there's a requirements.txt in the payload, add it to the dependencies
    fileslist = []
    try:
        fileslist = metadata['dlhub']['files']['other']
    except KeyError:
        pass

    if 'requirements.txt' in fileslist:
        dependencies.append("--requirement requirements.txt")

    model_location = None
    # If the model was uploaded using a signed URL, it will have a
    # transfer_method of S3 in its metadata.
    # If the model is being built from a repo, it will not have a
    # transfer_method, but will have a 'repository'
    if 'transfer_method' in metadata['dlhub']:
        if 'S3' in metadata['dlhub']['transfer_method']:
            model_location = metadata['dlhub']['transfer_method']['S3']
    if 'repository' in metadata:
        model_location = metadata['repository']
    if model_location is None:
        raise Exception("No model location exists in metadata")

    cs = ContainerSpec(
        name=metadata['dlhub']['shorthand_name'],
        pip=dependencies,
        python_version="3.7",
        payload_url=model_location,
        conda=[],
    )

    return cs


def check_container_build_status(funcx_client, container_uuid):
    # Set timeout to the internal timeout limit: 1800
    timeout_at = 1800
    i = 0
    # This loop means that we are blocking on the container build.
    while i < timeout_at:
        status = funcx_client.get_container_build_status(container_uuid)
        logger.debug(f"status is {status}")
        if status in ["ready", "failed"]:
            break
        sleep(5)
        i += 5
    else:
        raise Exception(f"Container Build Timeout after {timeout_at} seconds")
    return status


def search_ingest(task, header):
    """
    Ingest the servable data into a Globus Search index.

    Args:
        task (dict): the metadata of the servable to be ingested.
        header (str): the authorization header for the Globus Search Writer Lambda
    """
    logger.debug("Ingesting servable into Search.")

    # Construct the subject for the search index metadata as the container id
    iden = "https://dlhub.org/servables/{}".format(task['dlhub']['id'])

    # We need to construct a "gingest" document to submit to Globus Search
    # for ingestion https://docs.globus.org/api/search/reference/ingest/#gingest
    # For this, we need a copy of the metadata dict where all values are strings
    # to ingest to Globus Search
    ingestable = task
    d = [convert_dict(ingestable, str)]

    glist = []

    # Get model visibility from metadata; if there is no 'visible_to' entry
    # in the metadata, set the visibilty to default to ['public']
    visible_to = task['dlhub'].get('visible_to', ['public'])

    for document in d:
        gmeta_entry = mdf_toolbox.format_gmeta(document, visible_to, iden)
        glist.append(gmeta_entry)
    gingest = mdf_toolbox.format_gmeta(glist)

    logger.info("ingesting to search")
    logger.info(gingest)

    # POST the gingest document to the GLOBUS_SEARCH_WRITER_LAMBDA
    # which will ingest it to the search index.

    http_response = requests.post(
        GLOBUS_SEARCH_WRITER_LAMBDA,
        headers={"Authorization": header},
        json={'document_file': gingest})
    if http_response.status_code != 200:
        raise Exception(http_response.text)
    logger.info("Ingestion of {} to DLHub servables complete".format(iden))


def register_funcx(task, container_uuid, funcx_client):
    """Register the function and the container with funcX.

    Parameters
    ----------
    task : dict
        A dict of the task to publish
    container_uuid:  str
    funcx_client:  the funcx client to register with

    Returns
    -------
    str
        The funcX function id
    """

    fxc = funcx_client

    try:
        description = task['datacite']['descriptions'][0]['description']
    except Exception:
        description = f"A container for the DLHub model {task['dlhub']['shorthand_name']}"

    # The Container Service registers the container w/ funcx
    # Register a function
    funcx_id = fxc.register_function(dlhub_run, function_name=task['dlhub']['name'],
                                     container_uuid=container_uuid, description=description, public=True)

    return funcx_id


def dlhub_run(event):
    """Invoke the DLHub servable

    This function is the one registered with funcx to run the servable.
    """
    import json
    import time
    import os

    from os.path import expanduser
    path = expanduser("~")
    os.chdir(path)

    # Check to see if event is from old client
    if 'data' in event:
        raise ValueError('Upgrade your DLHub SDK to a newer version: pip install -U dlhub_sdk')

    start = time.time()
    global shim
    if "shim" not in globals():
        from home_run import create_servable
        with open("dlhub.json") as fp:
            shim = create_servable(json.load(fp))
    x = shim.run(event["inputs"],
                 debug=event.get("debug", False),
                 parameters=event.get("parameters", None))
    end = time.time()
    return (x, (end-start) * 1000)


def convert_dict(data, conversion_function=str):
    """
    Convert dict to string representations for publishing
    Recursively traverse the dict to ensure that all values are string
    representations (or dicts or lists that contain only string representations)

    Brought over from the DLHub Service ingestion scripts at:
       https://github.com/DLHub-Argonne/dlhub_service/blob/a04fc9ed683f92c1e8549ac539a406f306ed2eff/ingestion/publish_dockerize.py#L224

    Parameters:
        data  -- your object to be string-ified
        conversion_function  -- defaults to str.

    Returns:
        a deep copy of the original object, where all terminal values
        are strings.

    """
    if type(data) is dict:
        string_dict = {}
        for k, v in data.items():
            if type(v) is dict:
                string_dict[k] = convert_dict(v, conversion_function)
            elif type(v) is list:
                string_dict[k] = [convert_dict(item, conversion_function) for item in data[k]]
            else:
                string_dict[k] = conversion_function(v)
        return string_dict
    elif type(data) is list:
        return [convert_dict(item, conversion_function) for item in data]
    else:
        return conversion_function(data)


def get_dlhub_file(repository):
    """
    Use the github rest api to ensure the dlhub.json file exists.

    :param repository:
    :return:
    """
    # Github.get_repo() wants just the username/reponame (or orgname/reponame)
    # so we parse the URL to get this
    repo = repository.replace("https://github.com/", "")
    repo = repo.replace(".git", "")

    try:
        g = github.Github()
        r = g.get_repo(repo)
        contents = r.get_contents("dlhub.json")
        decoded = base64.b64decode(contents.content)
        return json.loads(decoded)
    except github.UnknownObjectException as e:
        raise Exception(f"dlhub.json not found in {repo} or {repo} itself not found") from e
    except Exception as e:
        raise Exception(f"dlhub.json could not be retrieved from {repo} due to {e}")


def update_servable_zip_with_metadata(servablezip, metadata):

    with ZipFile(servablezip, mode="a") as zf:
        zf.writestr('dlhub.json', json.dumps(metadata))
