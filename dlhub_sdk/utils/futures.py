"""Tools for dealing with asynchronous execution"""
from globus_sdk import GlobusAPIError
from concurrent.futures import Future
from threading import Thread
from time import sleep
import json


class DLHubFuture(Future):
    """Utility class for simplifying asynchronous execution in DLHub"""

    def __init__(self, client, task_id: str, ping_interval: float):
        """
        Args:
             client (DLHubClient): Already-initialized client, used to check
             task_id (str): Set the task ID of the
             ping_interval (float): How often to ping the server to check status in seconds
        """
        super().__init__()
        self.client = client
        self.task_id = task_id
        self.ping_interval = ping_interval

        # Once you create this, the task has already started
        self.set_running_or_notify_cancel()

        # Forcing the ping interval to be no less than 1s
        if ping_interval < 1:
            assert AttributeError('Ping interval must be at least 1 second')

        # Start a thread that polls status
        self._checker_thread = Thread(target=DLHubFuture._ping_server, args=(self,))
        self._checker_thread.start()

    def _ping_server(self):
        while True:
            sleep(self.ping_interval)
            try:
                if not self.running():
                    break
            except GlobusAPIError:
                # Keep pinging even if the results fail
                continue

    def running(self):
        if super().running():
            # If the task isn't already completed, check if it is still running
            status = self.client.get_task_status(self.task_id)
            # TODO (lw): What if the task fails on the server end? Do we have a "FAILURE" status?
            if status['status'] == 'COMPLETED':
                self.set_result(json.loads(status['result']))
                return False
            return True
        return False

    def stop(self):
        """Stop the execution of the function"""
        # TODO (lw): Should be attempt to cancel the execution of the task on DLHub?
        self.set_exception(Exception('Cancelled by user'))
