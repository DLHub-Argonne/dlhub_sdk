import json
import os
from tempfile import mkstemp

import requests
import globus_sdk

from typing import Union, Any, Optional
from globus_sdk.base import BaseClient, slash_join
from mdf_toolbox import login, logout
from mdf_toolbox.globus_search.search_helper import SEARCH_LIMIT

from funcx.sdk.client import FuncXClient

from dlhub_sdk.config import DLHUB_SERVICE_ADDRESS, CLIENT_ID
from dlhub_sdk.utils.futures import DLHubFuture
from dlhub_sdk.utils.schemas import validate_against_dlhub_schema
from dlhub_sdk.utils.search import DLHubSearchHelper, get_method_details, filter_latest


# Directory for authentication tokens
_token_dir = os.path.expanduser("~/.dlhub/credentials")


class DLHubClient(BaseClient):
    """Main class for interacting with the DLHub service

    Holds helper operations for performing common tasks with the DLHub service. For example,
    `get_servables` produces a list of all servables registered with DLHub.

    For most cases, we recommend creating a new DLHubClient by calling ``DLHubClient.login``.
    This operation will check if you have saved any credentials to disk before using the CLI or SDK
    and, if not, get new credentials and save them for later use.
    For cases where disk access is unacceptable, you can create the client by creating an authorizer
    following the
    `tutorial for the Globus SDK <https://globus-sdk-python.readthedocs.io/en/stable/tutorial/>`_
    and providing that authorizer to the initializer (e.g., ``DLHubClient(auth)``)"""

    def __init__(self, dlh_authorizer=None, search_client=None, http_timeout=None,
                 force_login=False, fx_authorizer=None, openid_authorizer=None, **kwargs):
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
            no_local_server (bool): Disable spinning up a local server to automatically
                copy-paste the auth code. THIS IS REQUIRED if you are on a remote server.
                When used locally with no_local_server=False, the domain is localhost with
                a randomly chosen open port number.
                **Default**: ``True``.
            fx_authorizer (:class:`GlobusAuthorizer
                            <globus_sdk.authorizers.base.GlobusAuthorizer>`):
                An authorizer instance used to communicate with funcX.
                If ``None``, will be created.
            openid_authorizer (:class:`GlobusAuthorizer
                            <globus_sdk.authorizers.base.GlobusAuthorizer>`):
                An authorizer instance used to communicate with OpenID.
                If ``None``, will be created.
            no_browser (bool): Do not automatically open the browser for the Globus Auth URL.
                Display the URL instead and let the user navigate to that location manually.
                **Default**: ``True``.
        Keyword arguments are the same as for BaseClient.
        """
        if force_login or not dlh_authorizer or not search_client \
                or not fx_authorizer or not openid_authorizer:
            fx_scope = "https://auth.globus.org/scopes/facd7ccc-c5f4-42aa-916b-a0e270e2c2a9/all"
            auth_res = login(services=["search", "dlhub",
                                       fx_scope, "openid"],
                             app_name="DLHub_Client",
                             make_clients=False,
                             client_id=CLIENT_ID,
                             clear_old_tokens=force_login,
                             token_dir=_token_dir,
                             no_local_server=kwargs.get("no_local_server", True),
                             no_browser=kwargs.get("no_browser", True))
            # openid_authorizer = auth_res["openid"]
            dlh_authorizer = auth_res["dlhub"]
            fx_authorizer = auth_res[fx_scope]
            openid_authorizer = auth_res['openid']
            search_authorizer = auth_res['search']
            self._fx_client = FuncXClient(force_login=force_login,
                                          fx_authorizer=fx_authorizer,
                                          search_authorizer=search_authorizer,
                                          openid_authorizer=openid_authorizer,
                                          no_local_server=kwargs.get("no_local_server", True),
                                          no_browser=kwargs.get("no_browser", True),
                                          funcx_service_address='https://api.funcx.org/v1')
            self._search_client = globus_sdk.SearchClient(authorizer=search_authorizer,
                                                          http_timeout=5 * 60)

        else:
            self._search_client = search_client
        # funcX endpoint to use
        self.fx_endpoint = '86a47061-f3d9-44f0-90dc-56ddc642c000'
        # self.fx_endpoint = '2c92a06a-015d-4bfa-924c-b3d0c36bdad7'
        self.fx_cache = {}
        super(DLHubClient, self).__init__("DLHub", environment='dlhub',
                                          authorizer=dlh_authorizer,
                                          http_timeout=http_timeout,
                                          base_url=DLHUB_SERVICE_ADDRESS,
                                          **kwargs)

    def logout(self):
        """Remove credentials from your local system"""
        logout()

    @property
    def query(self):
        """Access a query of the DLHub Search repository"""
        return DLHubSearchHelper(search_client=self._search_client)

    def get_username(self):
        """Get the username associated with the current credentials"""

        res = self.get('/namespaces')
        return res.data['namespace']

    def get_servables(self, only_latest_version=True):
        """Get all of the servables available in the service

        Args:
            only_latest_version (bool): Whether to only return the latest version of each servable
        Returns:
            ([list]) Complete metadata for all servables found in DLHub
        """

        # Get all of the servables
        results, info = self.query.match_field('dlhub.type', 'servable')\
            .add_sort('dlhub.owner', ascending=True).add_sort('dlhub.name', ascending=False)\
            .add_sort('dlhub.publication_date', ascending=False).search(info=True)
        if info['total_query_matches'] > SEARCH_LIMIT:
            raise RuntimeError('DLHub contains more servables than we can return in one entry. '
                               'DLHub SDK needs to be updated.')

        if only_latest_version:
            # Sort out only the most recent versions (they come first in the sorted list
            names = set()
            output = []
            for r in results:
                name = r['dlhub']['shorthand_name']
                if name not in names:
                    names.add(name)
                    output.append(r)
            results = output

        # Add these to the cache
        for r in results:
            self.fx_cache[r['dlhub']['shorthand_name']] = r['dlhub']['funcx_id']

        return results

    def list_servables(self):
        """Get a list of the servables available in the service

        Returns:
            [string]: List of all servable names in username/servable_name format
        """

        servables = self.get_servables(only_latest_version=True)
        return [x['dlhub']['shorthand_name'] for x in servables]

    def get_task_status(self, task_id):
        """Get the status of a DLHub task.

        Args:
            task_id (string): UUID of the task
        Returns:
            dict: status block containing "status" key.
        """

        r = self._fx_client.get_task(task_id)
        return r

    def describe_servable(self, name):
        """Get the description for a certain servable

        Args:
            name (string): DLHub name of the servable of the form <user>/<servable_name>
        Returns:
            dict: Summary of the servable
        """
        split_name = name.split('/')
        if len(split_name) < 2:
            raise AttributeError('Please enter name in the form <user>/<servable_name>')

        # Create a query for a single servable
        query = self.query.match_servable('/'.join(split_name[1:]))\
            .match_owner(split_name[0]).add_sort("dlhub.publication_date", False)\
            .search(limit=1)

        # Raise error if servable is not found
        if len(query) == 0:
            raise AttributeError('No such servable: {}'.format(name))
        return query[0]

    def describe_methods(self, name, method=None):
        """Get the description for the method(s) of a certain servable

        Args:
            name (string): DLHub name of the servable of the form <user>/<servable_name>
            method (string): Optional: Name of the method
        Returns:
             dict: Description of a certain method if ``method`` provided, all methods
                if the method name was not provided.
        """

        metadata = self.describe_servable(name)
        return get_method_details(metadata, method)

    def run(self, name, inputs,
            asynchronous=False, async_wait=5,
            timeout: Optional[float] = None) -> Union[Any, DLHubFuture]:
        """Invoke a DLHub servable

        Args:
            name (string): DLHub name of the servable of the form <user>/<servable_name>
            inputs: Data to be used as input to the function. Can be a string of file paths or URLs
            asynchronous (bool): Whether to return from the function immediately or
                wait for the execution to finish.
            async_wait (float): How many seconds to wait between checking async status
            timeout (float): How long to wait for a result to return.
                Only used for synchronous calls
        Returns:
            Results of running the servable. If asynchronous, then a DLHubFuture holding the result
        """

        if name not in self.fx_cache:
            # Look it up and add it to the cache, this will raise an exception if not found.
            serv = self.describe_servable(name)
            self.fx_cache.update({name: serv['dlhub']['funcx_id']})

        funcx_id = self.fx_cache[name]
        payload = {'data': inputs}
        task_id = self._fx_client.run(payload, endpoint_id=self.fx_endpoint, function_id=funcx_id)

        # Return the result
        future = DLHubFuture(self, task_id, async_wait)
        return future.result(timeout=timeout) if not asynchronous else future

    def run_serial(self, servables, inputs, async_wait=5):
        """Invoke each servable in a serial pipeline.
        This function accepts a list of servables and will run each one,
        passing the output of one as the input to the next.

        Args:
             servables (list): A list of servable strings
             inputs: Data to pass to the first servable
             asycn_wait (float): Seconds to wait between status checks
        Returns:
            Results of running the servable
        """
        if not isinstance(servables, list):
            print("run_serial requires a list of servables to invoke.")

        serv_data = inputs
        for serv in servables:
            serv_data = self.run(serv, serv_data, async_wait=async_wait)
        return serv_data

    def get_result(self, task_id, verbose=False):
        """Get the result of a task_id

        Args:
            task_id str: The task's uuid
            verbose bool: whether or not to return the full dlhub response
        Returns:
            Reult of running the servable
        """

        result = self._fx_client.get_result(task_id)
        if isinstance(result, tuple) and not verbose:
            result = result[0]
        return result

    def publish_servable(self, model):
        """Submit a servable to DLHub

        If this servable has not been published before, it will be assigned a unique identifier.

        If it has been published before (DLHub detects if it has an identifier), then DLHub
        will update the servable to the new version.

        Args:
            model (BaseMetadataModel): Servable to be submitted
        Returns:
            (string): Task ID of this submission, used for checking for success
        """

        # Get the metadata
        metadata = model.to_dict(simplify_paths=True)

        # Mark the method used to submit the model
        metadata['dlhub']['transfer_method'] = {'POST': 'file'}

        # Validate against the servable schema
        validate_against_dlhub_schema(metadata, 'servable')

        # Wipe the fx cache so we don't keep reusing an old servable
        self.clear_funcx_cache()

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
            (string): Task ID of this submission, used for checking for success
        """

        # Publish to DLHub
        metadata = {"repository": repository}

        # Wipe the fx cache so we don't keep reusing an old servable
        self.clear_funcx_cache()

        response = self.post('publish_repo', json_body=metadata)

        task_id = response.data['task_id']
        return task_id

    def search(self, query, advanced=False, limit=None, only_latest=True):
        """Query the DLHub servable library

        By default, the query is used as a simple plaintext search of all model metadata.
        Optionally, you can provided an advanced query on any of the indexed fields in
        the DLHub model metadata by setting :code:`advanced=True` and following the guide for
        constructing advanced queries found in the
        `Globus Search documentation <https://docs.globus.org/api/search/search/#query_syntax>`_.

        Args:
             query (string): Query to be performed
             advanced (bool): Whether to perform an advanced query
             limit (int): Maximum number of entries to return
             only_latest (bool): Whether to return only the latest version of the model
        Returns:
            ([dict]): All records matching the search query
        """

        results = self.query.search(query, advanced=advanced, limit=limit)
        return filter_latest(results) if only_latest else results

    def search_by_servable(self, servable_name=None, owner=None, version=None,
                           only_latest=True, limit=None, get_info=False):
        """Search by the ownership, name, or version of a servable

        Args:
            servable_name (str): The name of the servable. **Default**: None, to match
                    all servable names.
            owner (str): The name of the owner of the servable. **Default**: ``None``,
                    to match all owners.
            version (int): Model version, which corresponds to the date when the
                servable was published. **Default**: ``None``, to match all versions.
            only_latest (bool): When ``True``, will only return the latest version
                    of each servable. When ``False``, will return all matching versions.
                    **Default**: ``True``.
            limit (int): The maximum number of results to return.
                    **Default:** ``None``, for no limit.
            get_info (bool): If ``False``, search will return a list of the results.
                    If ``True``, search will return a tuple containing the results list
                    and other information about the query.
                    **Default:** ``False``.

        Returns:
            If ``info`` is ``False``, *list*: The search results.
            If ``info`` is ``True``, *tuple*: The search results,
            and a dictionary of query information.
        """
        if not servable_name and not owner and not version:
            raise ValueError("One of 'servable_name', 'owner', or 'publication_date' is required.")

        # Perform the query
        results, info = (self.query.match_servable(servable_name=servable_name, owner=owner,
                                                   publication_date=version)
                             .search(limit=limit, info=True))

        # Filter out the latest models
        if only_latest:
            results = filter_latest(results)

        if get_info:
            return results, info
        return results

    def search_by_authors(self, authors, match_all=True, limit=None, only_latest=True):
        """Execute a search for servables from certain authors.

        Authors in DLHub may be different than the owners of the servable and generally are
        the people who developed functionality of a certain servable (e.g., the creators
        of the machine learning model used in a servable).

        If you want to search by ownership, see :meth:`search_by_servable`

        Args:
            authors (str or list of str): The authors to match. Names must be in
                "Family Name, Given Name" format
            match_all (bool): If ``True``, will require all authors be on any results.
                    If ``False``, will only require one author to be in results.
                    **Default**: ``True``.
            limit (int): The maximum number of results to return.
                    **Default:** ``None``, for no limit.
            only_latest (bool): When ``True``, will only return the latest version
                    of each servable. When ``False``, will return all matching versions.
                    **Default**: ``True``.

        Returns:
            [dict]: List of servables from the desired authors
        """
        results = self.query.match_authors(authors, match_all=match_all).search(limit=limit)
        return filter_latest(results) if only_latest else results

    def search_by_related_doi(self, doi, limit=None, only_latest=True):
        """Get all of the servables associated with a certain publication

        Args:
            doi (string): DOI of related paper
            limit (int): Maximum number of results to return
            only_latest (bool): Whether to return only the most recent version of the model
        Returns:
            [dict]: List of servables from the requested paper
        """

        results = self.query.match_doi(doi).search(limit=limit)
        return filter_latest(results) if only_latest else results

    def clear_funcx_cache(self, servable=None):
        """Remove functions from the cache. Either remove a specific servable or wipe the whole cache.

        Args:
            Servable: str
                The name of the servable to remove. Default None
        """

        if servable:
            del(self.fx_cache[servable])
        else:
            self.fx_cache = {}

        return self.fx_cache
