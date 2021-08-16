from dlhub_sdk.utils.futures import DLHubFuture
from dlhub_sdk.client import DLHubClient
from unittest import TestCase, expectedFailure

from mdf_connect_client import MDFConnectClient
import mdf_toolbox


#github specific declarations
# client_id = os.getenv('CLIENT_ID')
# client_secret = os.getenv('CLIENT_SECRET')

fx_scope = "https://auth.globus.org/scopes/facd7ccc-c5f4-42aa-916b-a0e270e2c2a9/all"

services=[
        "search",
        "dlhub",
        fx_scope,
        "openid"]

auth_res = mdf_toolbox.confidential_login(client_id="b6544309-da65-4476-8259-300a7dbd7322",
                                        client_secret="ULR0Kr34F8glsslBw76MQoTYR+Mwebo3DjSrqVRd+DM=",
                                        services=services, make_clients=True)


# ID of a task that has completed in DLHub
completed_task = 'b8e51bc6-4081-4ec9-9e3b-b0e52198c08d'


class TestFutures(TestCase):

    @expectedFailure
    def test_future(self):
        client = DLHubClient(
            dlh_authorizer = auth_res["dlhub"], fx_authorizer = auth_res[fx_scope],
            openid_authorizer = auth_res['openid'], search_client = auth_res['search'],
            force_login=False, http_timeout=10
        )
        future = DLHubFuture(client, completed_task, 1)
        self.assertFalse(future.running())
        self.assertTrue(future.done())
        self.assertEquals({}, future.result())
