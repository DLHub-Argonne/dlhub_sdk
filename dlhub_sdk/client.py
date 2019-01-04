from dlhub_sdk.utils.schemas import validate_against_dlhub_schema
from dlhub_sdk.utils.auth import do_login_flow, make_authorizer
from dlhub_sdk.config import check_logged_in, DLHUB_SERVICE_ADDRESS
from globus_sdk.base import BaseClient
from tempfile import mkstemp
import pickle as pkl
import pandas as pd
import botocore
import requests
import codecs
import boto3
import uuid
import os


# TODO: Make this inherit from BaseClient in globus_sdk
class DLHubClient(BaseClient):
    """Main class for interacting with the DLHub service

    Holds helper operations for performing common tasks with the DLHub service. For example,
    `get_servables` produces a list of all servables registered with DLHub."""

    def __init__(self, authorizer, http_timeout=None, **kwargs):
        """Initialize the client

        Args:
            authorizer (:class:`GlobusAuthorizer <globus_sdk.authorizers.base.GlobusAuthorizer>`):
                An authorizer instance used to communicate with DLHub
            http_timeout (int): Timeout for any call to service in seconds. (default is no timeout)
        Keyword arguments are the same as for BaseClient
        """
        super(DLHubClient, self).__init__("DLHub", environment='dlhub', authorizer=authorizer,
                                          http_timeout=http_timeout, base_url=DLHUB_SERVICE_ADDRESS,
                                          **kwargs)

    @classmethod
    def login(cls, force=True, **kwargs):
        """Create a DLHubClient with credentials

        Either uses the credentials already saved on the system or, if no credentials are present
        or ``force=True``, runs a login procedure to get new credentials

        Keyword arguments are passed to the DLHubClient constructor

        Args:
            force (bool): Whether to force a login to get new credentials
        Returns:
            (DLHubClient) A client complete with proper credentials
        """

        # If not logged in or `force`, get credentials
        if not force and check_logged_in():
            # Asks for user credentials, saves the resulting Auth tokens to disk
            do_login_flow()

        # Makes an authorizer
        rf_authorizer = make_authorizer()

        return DLHubClient(rf_authorizer, **kwargs)

    def _get_servables(self):
        """Get all of the servables available in the service

        Returns:
            (pd.DataFrame) Summary of all the models available in the service
        """
        r = requests.get("{service}/servables".format(
            service=DLHUB_SERVICE_ADDRESS), timeout=self._http_timeout)
        return pd.DataFrame(r.json())

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
        return df_tmp[['name', 'uuid']]

    def get_id_by_name(self, name):
        """Get the ID of a DLHub servable by name

        Args:
            name (string): Name of the servable
        Returns:
            (string) UUID of the servable
        """

        df_tmp = self._get_servables()
        serv = df_tmp[df_tmp.name == name]
        return serv.iloc[0]['uuid']

    def get_task_status(self, task_id):
        """Get the status of a DLHub task.

        Args:
            task_id (string): UUID of the task
        Returns:
            (dict) status block containing "status" key.
        """

        r = requests.get("{service}/{task_id}/status".format(
            service=DLHUB_SERVICE_ADDRESS, task_id=task_id), timeout=self.timeout)
        return r.json()

    def describe_servable(self, servable_id=None, servable_name=None):
        """Get a list of the servables available in the service
        Args:
            servable_id (string): ID of the servable
            servable_name (string): Name of the servable
        Returns:
            (pd.DataFrame) Summary of the servable
        """

        df_tmp = self._get_servables()
        serv = pd.DataFrame({})
        df_tmp = df_tmp[['name', 'uuid', 'description', 'input', 'output', 'author','status']]
        if servable_id:
            serv = df_tmp[df_tmp.uuid == servable_id]
        elif servable_name:
            serv = df_tmp[df_tmp.name == servable_name]
        return serv.iloc[0]

    def run(self, servable_id, inputs, input_type='json'):
        """Invoke a DLHub servable

        Args:
            servable_id (string): UUID of the servable
            inputs: Data to be used as input to the function. Can be a string of file paths or URLs
            input_type (string): How to send the data to DLHub. Can be "python" (which pickles
                the data), "json" (which uses JSON to serialize the data), or "files" (which
                sends the data as files).
        Returns:
            Reply from the service
        """
        servable_path = '{service}/servables/{servable_id}/run'.format(
            service=DLHUB_SERVICE_ADDRESS, servable_id=servable_id)

        # Prepare the data to be sent to DLHub
        if input_type == 'python':
            data = {'python': codecs.encode(pkl.dumps(inputs), 'base64').decode()}
        elif input_type == 'json':
            data = {'data': inputs}
        elif input_type == 'files':
            raise NotImplementedError('Files support is not yet implemented')
        else:
            raise ValueError('Input type not recognized: {}'.format(input_type))

        # Send the data to DLHub
        r = requests.post(servable_path, json=data, timeout=self._http_timeout)
        if r.status_code is not 200:
            raise Exception(r)

        # Return the result
        return r.json()

    def publish_servable(self, model):
        """Submit a servable to DLHub

        If this servable has not been published before, it will be assigned a unique identifier.

        If it has been published before (DLHub detects if it has an identifier), then DLHub
        will update the model to the new version.

        Args:
            model (BaseMetadataModel): Model to be submitted
        Returns:
            (string) Task ID of this submission, used for checking for success
        """

        # If unassigned, give the model a UUID
        if model.dlhub_id is None:
            model.assign_dlhub_id()

        # Get the metadata
        metadata = model.to_dict(simplify_paths=True)

        # Stage data for DLHub to access
        staged_path = self._stage_data(model)
        if not staged_path:
            return
        
        # Mark the method used to submit the model
        metadata['dlhub']['transfer_method'] = {'S3': staged_path}

        # Validate against the servable schema
        validate_against_dlhub_schema(metadata, 'servable')

        # Publish to DLHub
        response = requests.post('{service}/publish'.format(service=DLHUB_SERVICE_ADDRESS),
                                 json=metadata, timeout=self.timeout)

        task_id = response.json()['task_id']
        return task_id

    def publish_repository(self, repository):
        """Submit a repository to DLHub for publication

        Args:
            repository (string): Repository to publish
        Returns:
            (string) Task ID of this submission, used for checking for success
        """


        # Get the metadata
        # metadata = model.to_dict(simplify_paths=True)
        # Validate against the servable schema
        # validate_against_dlhub_schema(metadata, 'servable')

        # Publish to DLHub
        metadata = {"repository": repository}
        response = requests.post('{service}/publish_repo'.format(service=DLHUB_SERVICE_ADDRESS),
                                 json=metadata, timeout=self.timeout)

        task_id = response.json()['task_id']
        return task_id

    def _stage_data(self, servable):
        """
        Stage data to the DLHub service.

        :param data_path: The data to upload
        :return str: path to the data on S3
        """
        s3 = boto3.resource('s3')

        # Generate a uuid to deposit the data
        dest_uuid = str(uuid.uuid4())
        dest_dir = 'servables/'
        bucket_name = 'dlhub-anl'

        fp, zip_filename = mkstemp('.zip')
        os.close(fp)
        os.unlink(zip_filename)

        try:
            servable.get_zip_file(zip_filename)

            destpath = os.path.join(dest_dir, dest_uuid, zip_filename.split("/")[-1])
            print("Uploading: {}".format(zip_filename))
            res = s3.Object(bucket_name, destpath).put(ACL="public-read",
                                                       Body=open(zip_filename, 'rb'))
            staged_path = os.path.join("s3://", bucket_name, dest_dir, dest_uuid)
            return staged_path
        except botocore.exceptions.NoCredentialsError as e:
            print("Failed to load AWS credentials. Please check they are configured with 'aws configure'.")
            return None
        except Exception as e:
            print("Publication error: {}".format(e))
        finally:
            os.unlink(zip_filename)
