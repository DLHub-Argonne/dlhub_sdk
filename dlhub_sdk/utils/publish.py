import logging
import json
import os
import requests
import globus_sdk

from funcx.sdk.client import FuncXClient
from funcx import ContainerSpec
from time import sleep
from github import Github
import base64

import mdf_toolbox
import urllib

#Uncomment if we are trying to mint identifiers
# from identifiers_client.identifiers_api import identifiers_client, IdentifierClient
# from identifiers_client.config import config

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
    except:
        # There are no python dependencies
        pass

    model_location = None
    if 'transfer_method' in metadata['dlhub']:
        if 'S3' in metadata['dlhub']['transfer_method']:
            model_location = metadata['dlhub']['transfer_method']['S3']
        elif 'POST' in metadata['dlhub']['transfer_method']:
            model_location = metadata['dlhub']['transfer_method']['path']
    if 'repository' in metadata:
        model_location = metadata['repository']
    cs = ContainerSpec(
        name=metadata['dlhub']['shorthand_name'],
        pip=dependencies,
        python_version="3.7",
        payload_url=model_location,
        conda=[],
    )

    return cs


def search_ingest(task, header):
    """
    Ingest the servable data into a Globus Search index.

    Args:
        task (dict): the task description.
    """
    logger.debug("Ingesting servable into Search.")

#    idx = "dlhub"
    # idx = '847c9105-18a0-4ffb-8a71-03dd76dfcc9d'
    iden = "https://dlhub.org/servables/{}".format(task['dlhub']['id'])
    # index = mdf_toolbox.translate_index(idx)

    ingestable = task
    d = [convert_dict(ingestable, str)]

    glist = []
    visible_to = task['dlhub'].get('visible_to', ['public'])

    # Add public so it isn't an empty list
    if len(visible_to) == 0:
        visible_to = ['public']

    for document in d:
        gmeta_entry = mdf_toolbox.format_gmeta(document, visible_to, iden)
        glist.append(gmeta_entry)
    gingest = mdf_toolbox.format_gmeta(glist)

    logger.info("ingesting to search")
    logger.info(gingest)

    GLOBUS_SEARCH_WRITER_LAMBDA = "https://7v5g6s33utz4l7jx6dkxuh77mu0cqdhb.lambda-url.us-east-2.on.aws/"

    # Get the authorization header token (string for the headers dict)
    #header = self.authorizer.get_authorization_header()

    http_response = requests.post(
        GLOBUS_SEARCH_WRITER_LAMBDA,
        headers={"Authorization": header},
        json={'document_file': gingest})
    if http_response.status_code != 200:
        raise Exception(http_response.text)
    logger.info("Ingestion of {} to DLHub servables complete".format(iden))


def mint_identifier(task):
    """Mint a new identifier and return it."""
    identifiers_namespace = '1EGOGHSs9RAtq'
    identifier = None
    logger.debug("Creating identifier")
    try:
        # client = identifiers_client(config)
        serv_location = "https://%s%s" % ("dlhub.org/servables/", task['dlhub']['id'])
        # safe encode the location
        serv_location = urllib.parse.quote_plus(serv_location, safe='')
        # can't be too safe!
        serv_location = urllib.parse.quote_plus(serv_location, safe='')
        # Create the petrel link
        serv_location = f'https://petreldata.net/dlhub/detail/{serv_location}'
        visible_to = ['public']

        dataset_identifier = client.create_identifier(
            namespace=identifiers_namespace,
            location=[serv_location],
            metadata={
                'uuid': task['dlhub']['id'],
                'shorthand_name': task['dlhub']['shorthand_name']
            },
            landing_page=serv_location,
            visible_to=visible_to)

        res = dataset_identifier.data
        identifier = res['identifier']
        logger.debug(f"Created identifier: {identifier}")
    except Exception as e:
        logger.error(e)
    return identifier


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

    description = f"A container for the DLHub model {task['dlhub']['shorthand_name']}"
    try:
        description = task['datacite']['descriptions'][0]['description']
    except:
        # It doesn't have a simple description
        pass
    # I believe that the Container Service registers the container w/ funcx
    # Register the container with funcX
    # container_id = fxc.register_container(task['dlhub']['ecr_uri'], 'docker', name=task['dlhub']['shorthand_name'],
    #                                      description=description)

    # Register a function
    funcx_id = fxc.register_function(dlhub_run, function_name=task['dlhub']['name'],
                                     container_uuid=container_uuid, description=description, public=True)

    # Whitelist the function on DLHub's endpoint
    #endpoint_uuid = '86a47061-f3d9-44f0-90dc-56ddc642c000'
    endpoint_uuid = '2238617a-8756-4030-a8ab-44ffb1446092'

    res = fxc.add_to_whitelist(endpoint_uuid, [funcx_id])
    print(res)
    return funcx_id


def dlhub_run(event):
    """Invoke the DLHub servable"""
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

    repo = repository.replace("https://github.com/", "")
    repo = repo.replace(".git", "")

    try:
        g = Github()
        r = g.get_repo(repo)
        contents = r.get_contents("dlhub.json")
        decoded = base64.b64decode(contents.content)
        return json.loads(decoded)
    except:
        return None
