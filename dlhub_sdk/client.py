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

    # ***********************************************
    # * Core functions
    # ***********************************************

    def match_field(self, field, value, required=True, new_group=False):
        """Add a ``field:value`` term to the query.
        Matches will have the ``value`` in the ``field``.

        Arguments:
            field (str): The field to check for the value.
                    The field must be namespaced according to Elasticsearch rules
                    using the dot syntax.
                    For example, ``"dlhub.name"`` is the ``name`` field
                    of the ``dlhub`` dictionary.
            value (str): The value to match.
            required (bool): If ``True``, will add term with ``AND``.
                    If ``False``, will use ``OR``. **Default:** ``True``.
            new_group (bool): If ``True``, will separate the term into a new parenthetical group.
                    If ``False``, will not.
                    **Default:** ``False``.

        Returns:
            DLHubClient: Self
        """
        self.__forge_client.match_field(field, value, required=required, new_group=new_group)
        return self

    def exclude_field(self, field, value, new_group=False):
        """Exclude a ``field:value`` term from the query.
        Matches will NOT have the ``value`` in the ``field``.

        Arguments:
            field (str): The field to check for the value.
                    The field must be namespaced according to Elasticsearch rules
                    using the dot syntax.
                    For example, ``"dlhub.name"`` is the ``name`` field
                    of the ``dlhub`` dictionary.
            value (str): The value to exclude.
            new_group (bool): If ``True``, will separate term the into a new parenthetical group.
                    If ``False``, will not.
                    **Default:** ``False``.

        Returns:
            DLHubClient: Self
        """
        self.__forge_client.exclude_field(field, value, new_group=new_group)
        return self

    def exclusive_match(self, field, value):
        """Match exactly the given value(s), with no other data in the field.

        Arguments:
            field (str): The field to check for the value.
                    The field must be namespaced according to Elasticsearch rules
                    using the dot syntax.
                    For example, ``"dlhub.name"`` is the ``name`` field
                    of the ``dlhub`` dictionary.
            value (str or list of str): The value(s) to match exactly.

        Returns:
            DLHubClient: Self
        """
        self.__forge_client.exclusive_match(field=field, value=value)
        return self

    def search(self, q=None, index=None, advanced=False, limit=None, info=False,
               reset_query=True, only_functions=False):
        """Execute a search and return the results.

        Args:
            q (str): The query to execute. **Default:** The current helper-formed query, if any.
                    There must be some query to execute.
            index (str): The Search index to search on. **Default:** The current index.
            advanced (bool): If ``True``, will submit query in "advanced" mode
                    to enable field matches and other advanced features.
                    If ``False``, only basic fulltext term matches will be supported.
                    **Default:** ``False`` if no helpers have been used to build the query, or
                    ``True`` if helpers have been used.
            limit (int): The maximum number of results to return.
                    **Default:** ``None``, for no limit.
            info (bool): If ``False``, search will return a list of the results.
                    If ``True``, search will return a tuple containing the results list
                    and other information about the query.
                    **Default:** ``False``.
            reset_query (bool): If ``True``, will destroy the current query after execution
                    and start a fresh one.
                    If ``False``, will keep the current query set.
                    **Default:** ``True``.
            only_functions (bool): If ``True``, will filter the result entries and only
                    return the ``servable.methods`` information, if present.
                    If ``False``, will return the full result entries.
                    **Default**: ``False``.

        Returns:
            If ``info`` is ``False``, *list*: The search results.
            If ``info`` is ``True``, *tuple*: The search results,
            and a dictionary of query information.
        """
        res = self.__forge_client.search(q=q, index=index, advanced=advanced, limit=limit,
                                         info=info, reset_query=reset_query)
        # Filter out everything except servable.methods if requested
        if only_functions:
            entries = res[0] if info else res
            res = [entry["servable"]["methods"] for entry in entries
                   if entry.get("servable", {}).get("methods", None)]
        return res

    def show_fields(self, index=None):
        """Retrieve and return the mapping for the given metadata block.

        Arguments:
            index (str): The Search index to map. **Default:** The current index.

        Returns:
            dict: ``field:datatype`` pairs.
        """
        return self.__forge_client.show_fields(block="all", index=index)

    def current_query(self):
        """Return the current query string.

        Returns:
            str: The current query.
        """
        return self.__forge_client.current_query()

    def reset_query(self):
        """Destroy the current query and create a fresh one.
        This method should not be chained.

        Returns:
            None
        """
        return self.__forge_client.reset_query()

    # ***********************************************
    # * Match field functions
    # ***********************************************

    def match_authors(self, authors, match_all=True):
        """Add authors to the query.

        Args:
            authors (str or list of str): The authors to match.
            match_all (bool): If ``True``, will require all authors be on any results.
                    If ``False``, will only require one author to be in results.
                    Default ``True``.

        Returns:
            DLHubClient: Self
        """
        if not authors:
            return self
        if isinstance(authors, str):
            authors = [authors]
        # First author should be in new group and required
        self.match_field(field="datacite.creators.creatorName", value=authors[0], required=True,
                         new_group=True)
        # Other authors should stay in that group
        for author in authors[1:]:
            self.match_field(field="datacite.creators.creatorName", value=author,
                             required=match_all, new_group=False)
        return self

    def match_domains(self, domains, match_all=True):
        """Add domains to the query.

        Args:
            domains (str or list of str): The domains to match.
            match_all (bool): If ``True``, will require all domains be on any results.
                    If ``False``, will only require one domain to be in results.
                    Default ``True``.

        Returns:
            DLHubClient: Self
        """
        if not domains:
            return self
        if isinstance(domains, str):
            domains = [domains]
        # First domain should be in new group and required
        self.match_field(field="dlhub.domains", value=domains[0], required=True, new_group=True)
        # Other domains should stay in that group
        for domain in domains[1:]:
            self.match_field(field="dlhub.domains", value=domain, required=match_all,
                             new_group=False)
        return self

    # ***********************************************
    # * Premade search functions
    # ***********************************************

    def search_by_authors(self, authors, match_all=True, index=None, limit=None, info=False):
        """Execute a search for the given authors.
        This method is equivalent to ``.match_authors(...).search(...)``.

        Note:
            This method will use terms from the current query, and resets the current query.

        Args:
            authors (str or list of str): The authors to match.
            match_all (bool): If ``True``, will require all authors be on any results.
                    If ``False``, will only require one author to be in results.
                    Default ``True``.
            index (str): The Search index to search on. **Default:** The current index.
            limit (int): The maximum number of results to return.
                    **Default:** ``None``, for no limit.
            info (bool): If ``False``, search will return a list of the results.
                    If ``True``, search will return a tuple containing the results list
                    and other information about the query.
                    **Default:** ``False``.

        Returns:
            If ``info`` is ``False``, *list*: The search results.
            If ``info`` is ``True``, *tuple*: The search results,
            and a dictionary of query information.
        """
        return self.match_authors(authors, match_all=match_all).search(index=index,
                                                                       limit=limit, info=info)
