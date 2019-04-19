from dlhub_sdk.utils.futures import DLHubFuture
from dlhub_sdk.client import DLHubClient
from unittest import TestCase

# ID of a task that has completed in DLHub
completed_task = 'b8e51bc6-4081-4ec9-9e3b-b0e52198c08d'


class TestFutures(TestCase):

    def test_future(self):
        client = DLHubClient()
        future = DLHubFuture(client, completed_task, 1)
        self.assertFalse(future.running())
        self.assertTrue(future.done())
        self.assertEquals({}, future.result())
