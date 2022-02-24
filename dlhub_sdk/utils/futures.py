"""Tools for dealing with asynchronous execution"""
from globus_sdk import GlobusAPIError
from concurrent.futures import Future
from threading import Thread
from time import sleep


class DLHubFuture(Future):
    """Utility class for simplifying asynchronous execution in DLHub"""

    def __init__(self, client, task_id: str, ping_interval: float, debug: bool):
        """
        Args:
             client: Already-initialized client, used to check
             task_id: Set the task ID of the
             ping_interval: How often to ping the server to check status in seconds
             debug: Whether to return the run metadata
        """
        super().__init__()
        self.client = client
        self.task_id = task_id
        self.ping_interval = ping_interval
        self.debug = debug

        # List of pending statuses returned by funcX.
        # TODO: Replace this once funcX stops raising exceptions when a task is pending.
        self.pending_statuses = ["received", "waiting-for-ep", "waiting-for-nodes",
                                 "waiting-for-launch", "running"]

        # Once you create this, the task has already started
        self.set_running_or_notify_cancel()

        # Forcing the ping interval to be no less than 1s
        if ping_interval < 1:
            assert AttributeError('Ping interval must be at least 1 second')

        # Start a thread that polls status
        self._checker_thread = Thread(target=DLHubFuture._ping_server, args=(self,), daemon=True)
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
            try:
                results = self.client.get_result(self.task_id, verbose=True)
            except Exception as e:
                # Check if it is "Task pending". funcX throws an exception on pending.
                if e.args[0] in self.pending_statuses:
                    return True

                # If not, something has gone wrong and we need to throw an exception
                else:
                    self.set_exception(e)
                    return False

            # If successfull, `status` now contains:
            #  (function_return, metadata), run_time
            (return_val, metadata), _ = results

            if not metadata['success']:
                self.set_exception(metadata['exc'])
            else:
                # If debug: then return return_val and metadata
                if self.debug:
                    self.set_result((return_val, metadata))
                else:
                    self.set_result(return_val)
                return False

        return False

    def stop(self):
        """Stop the execution of the function"""
        # TODO (lw): Should be attempt to cancel the execution of the task on DLHub?
        self.set_exception(Exception('Cancelled by user'))
