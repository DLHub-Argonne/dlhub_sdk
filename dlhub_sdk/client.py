import json
import os
from tempfile import mkstemp

from globus_sdk.base import BaseClient, slash_join
import jsonpickle
import mdf_forge
import mdf_toolbox
import pandas as pd
import requests

from dlhub_sdk.config import DLHUB_SERVICE_ADDRESS, CLIENT_ID, SEARCH_INDEX
from dlhub_sdk.utils.schemas import validate_against_dlhub_schema


class DLHubClient(BaseClient):
    """Main class for interacting with the DLHub service

    Holds helper operations for performing common tasks with the DLHub service. For example,
    `get_servables` produces a list of all servables registered with DLHub.

    For most cases, we recommend creating a new DLHubClient by calling ``DLHubClient.login``.
    This operation will check if you have saved any credentials to disk before using the CLI or SDK
    and, if not, get new credentials and save them for later use.
    For cases where disk access is unacceptable, you can create the client by creating an authorizer
    following the
    `tutorial for the Globus SDK <https://globus-sdk-python.readthedocs.io/en/stable/tutorial/>_
    and providing that authorizer to the initializer (e.g., ``DLHubClient(auth)``)"""

    def __init__(self, dlh_authorizer=None, search_client=None, http_timeout=None,
                 force_login=False, **kwargs):
        """Initialize the client

        Args:
            dlh_authorizer (:class:`GlobusAuthorizer
                            <globus_sdk.authorizers.base.GlobusAuthorizer>`):
                An authorizer instance used to communicate with DLHub.
                If ``None``, will be created.
            search_client (:class:`SearchClient <globus_sdk.SearchClient>`):
                An authenticated SearchClient to communicate with Globus Search.
                If ``None``, will be created.
            http_timeout (int): Timeout for any call to service in seconds. (default is no timeout)
            force_login (bool): Whether to force a login to get new credentials.
                A login will always occur if ``dlh_authorizer`` or ``search_client``
                are not provided.
        Keyword arguments are the same as for BaseClient.
        """
        if force_login or not dlh_authorizer or not search_client:
            auth_res = mdf_toolbox.login(services=["search", "dlhub"], app_name="DLHub_Client",
                                         client_id=CLIENT_ID, clear_old_tokens=force_login,
                                         token_dir=os.path.expanduser("~/.dlhub/credentials"))
            dlh_authorizer = auth_res["dlhub"]
            search_client = auth_res["search"]
        # Unused variable, will be used in future
        self.__forge_client = mdf_forge.Forge(index=SEARCH_INDEX, services=[],  # noqa: F841
                                              clients={"search": search_client})
        super(DLHubClient, self).__init__("DLHub", environment='dlhub', authorizer=dlh_authorizer,
                                          http_timeout=http_timeout, base_url=DLHUB_SERVICE_ADDRESS,
                                          **kwargs)

    @classmethod
    def login(cls, force=False, **kwargs):
        """Create a DLHubClient with credentials

        Either uses the credentials already saved on the system or, if no credentials are present
        or ``force=True``, runs a login procedure to get new credentials

        Keyword arguments are passed to the DLHubClient constructor

        Args:
            force (bool): Whether to force a login to get new credentials.
        Returns:
            (DLHubClient) A client complete with proper credentials.
        """
        auth_res = mdf_toolbox.login(services=["search", "dlhub"], app_name="DLHub_Client",
                                     token_dir=os.path.expanduser("~/.dlhub/credentials"),
                                     clear_old_tokens=force)
        return DLHubClient(dlh_authorizer=auth_res["dlhub"], search_client=auth_res["search"],
                           **kwargs)

    def _get_servables(self):
        """Get all of the servables available in the service

        Returns:
            (pd.DataFrame) Summary of all the models available in the service
        """

        r = self.get("servables")
        return pd.DataFrame(r.data)

    def get_servables(self):
        """Get all of the servables available in the service

        This is for backwards compatibility. Previous demos relied on this function
        prior to it being made an internal function.

        Returns:
            (pd.DataFrame) Summary of all the models available in the service
        """

        return self._get_servables()

    def list_servables(self):
        """Get a list of the servables available in the service

        Returns:
            (pd.DataFrame) Summary of all the models available in the service
        """
        df_tmp = self._get_servables()
        return df_tmp[['dlhub_name']]

    def get_task_status(self, task_id):
        """Get the status of a DLHub task.

        Args:
            task_id (string): UUID of the task
        Returns:
            (dict) status block containing "status" key.
        """

        r = self.get("{task_id}/status".format(task_id=task_id))
        return r.json()

    def describe_servable(self, author, name):
        """
        Get the description for a certain servable

        Args:
            author (string): Username of the owner of the servable
            name (string): Name of the servable
        Returns:
            (pd.DataFrame) Summary of the servable
        """

        df_tmp = self._get_servables()

        # Downselect to more useful information
        df_tmp = df_tmp[['name', 'description', 'input', 'output', 'author', 'status']]

        # Get the desired servable
        serv = df_tmp.query('name={name} AND author={author}'.format(name=name, author=author))
        return serv.iloc[0]

    def run(self, name, inputs, input_type='python'):
        """Invoke a DLHub servable

        Args:
            name (string): DLHub name of the model of the form <user>/<model_name>
            inputs: Data to be used as input to the function. Can be a string of file paths or URLs
            input_type (string): How to send the data to DLHub. Can be "python" (which pickles
                the data), "json" (which uses JSON to serialize the data), or "files" (which
                sends the data as files).
        Returns:
            Reply from the service
        """
        servable_path = 'servables/{name}/run'.format(name=name)

        # Prepare the data to be sent to DLHub
        if input_type == 'python':
            # data = {'python': codecs.encode(pkl.dumps(inputs), 'base64').decode()}
            data = {'python': jsonpickle.encode(inputs)}
        elif input_type == 'json':
            data = {'data': inputs}
        elif input_type == 'files':
            raise NotImplementedError('Files support is not yet implemented')
        else:
            raise ValueError('Input type not recognized: {}'.format(input_type))

        # Send the data to DLHub
        r = self.post(servable_path, json_body=data)
        if r.http_status != 200:
            raise Exception(r)

        # Return the result
        return r.data

    def publish_servable(self, model):
        """Submit a servable to DLHub

        If this servable has not been published before, it will be assigned a unique identifier.

        If it has been published before (DLHub detects if it has an identifier), then DLHub
        will update the model to the new version.

        Args:
            model (BaseMetadataModel): Servable to be submitted
        Returns:
            (string) Task ID of this submission, used for checking for success
        """

        # Get the metadata
        metadata = model.to_dict(simplify_paths=True)

        # Mark the method used to submit the model
        metadata['dlhub']['transfer_method'] = {'POST': 'file'}

        # Validate against the servable schema
        validate_against_dlhub_schema(metadata, 'servable')

        # Get the data to be submitted as a ZIP file
        fp, zip_filename = mkstemp('.zip')
        os.close(fp)
        os.unlink(zip_filename)
        try:
            model.get_zip_file(zip_filename)

            # Get the authorization headers
            headers = {}
            self.authorizer.set_authorization_header(headers)

            # Submit data to DLHub service
            with open(zip_filename, 'rb') as zf:
                reply = requests.post(
                    slash_join(self.base_url, 'publish'),
                    headers=headers,
                    files={
                        'json': ('dlhub.json', json.dumps(metadata), 'application/json'),
                        'file': ('servable.zip', zf, 'application/octet-stream')
                    }
                )

            # Return the task id
            if reply.status_code != 200:
                raise Exception(reply.text)
            return reply.json()['task_id']
        finally:
            os.unlink(zip_filename)

    def publish_repository(self, repository):
        """Submit a repository to DLHub for publication

        Args:
            repository (string): Repository to publish
        Returns:
            (string) Task ID of this submission, used for checking for success
        """

        # Publish to DLHub
        metadata = {"repository": repository}
        response = self.post('publish_repo', json_body=metadata)

        task_id = response.data['task_id']
        return task_id
