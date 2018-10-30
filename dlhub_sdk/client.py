from dlhub_sdk.utils.schemas import validate_against_dlhub_schema
from tempfile import mkstemp
import pandas as pd
import requests
import boto3
import uuid
import os


class DLHubClient:
    """Main class for interacting with the DLHub service

    Holds helper operations for performing common tasks with the DLHub service. For example,
    `get_servables` produces a list of all servables registered with DLHub."""
    service = "https://dlhub.org/api/v1"

    def __init__(self, timeout=None):
        """Initialize the client

        Args:
            timeout (int): Timeout for any call to service. (default is no timeout)
            """
        self.timeout = timeout

    def get_servables(self):
        """Get a list of the servables available in the service

        Returns:
            (pd.DataFrame) Summary of all the models available in the service
        """
        r = requests.get("{service}/servables".format(service=self.service), timeout=self.timeout)
        return pd.DataFrame(r.json())

    def get_id_by_name(self, name):
        """Get the ID of a DLHub servable by name

        Args:
            name (string): Name of the servable
        Returns:
            (string) UUID of the servable
        """
        r = requests.get("{service}/servables".format(service=self.service), timeout=self.timeout)
        df_tmp = pd.DataFrame(r.json())
        serv = df_tmp[df_tmp.name == name]
        return serv.iloc[0]['uuid']

    def run(self, servable_id, data):
        """Invoke a DLHub servable

        Args:
            servable_id (string): UUID of the servable
            data (dict): Dictionary of the data to send to the servable
        Returns:
            (pd.DataFrame): Reply from the service
        """
        servable_path = '{service}/servables/{servable_id}/run'.format(service=self.service,
                                                                       servable_id=servable_id)

        r = requests.post(servable_path, json=data, timeout=self.timeout)
        if r.status_code is not 200:
            raise Exception(r)
        return pd.DataFrame(r.json())

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
            model.assign_uuid()

        # Get the metadata
        metadata = model.to_dict(simplify_paths=True)

        # Validate against the servable schema
        validate_against_dlhub_schema(metadata, 'servable')

        # Stage data for DLHub to access
        staged_path = self._stage_data(model)
        # Mark the method used to submit the model
        metadata['dlhub']['transfer_method'] = {'S3': staged_path}

        # Publish to DLHub
        response = requests.post('{service}/publish'.format(service=self.service),
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
        except Exception as e:
            print("Publication error: {}".format(e))
        finally:
            os.unlink(zip_filename)
