"""Tools for interacting with the DLHub Search Index"""

from mdf_toolbox.globus_search.search_helper import SearchHelper
from globus_sdk import SearchClient
from warnings import warn


class DLHubSearchHelper(SearchHelper):
    """Helper class for building queries with DLHub"""

    def __init__(self, search_client: SearchClient, **kwargs):
        """Initialize the Helper

        Keyword arguments are passed to the underlying SearchHelper

        Args:
            search_client (SearchClient): Search client to use for authentication
        """
        super(DLHubSearchHelper, self).__init__("dlhub", search_client=search_client, **kwargs)

    def match_owner(self, owner):
        """Add a model owner to the query.

        Args:
            owner (str): The name of the owner of the model.

        Returns:
            DLHubSearchHelper: Self
        """
        if owner:
            self.match_field("dlhub.owner", owner)
        return self

    def match_servable(self, servable_name=None, owner=None, publication_date=None):
        """Add identifying model information to the query.
        If this method is called without any valid arguments, it will do nothing.

        Args:
            servable_name (str): The name of the model. **Default**: None, to match
                    all model names.
            owner (str): The name of the owner of the model. **Default**: ``None``,
                    to match all owners.
            publication_date (int): The UNIX timestamp for when the model was published.
                    **Default**: ``None``, to match all versions.

        Returns:
            DLHubSearchHelper: Self
        """
        if servable_name:
            self.match_field("dlhub.name", servable_name)
        if owner:
            self.match_owner(owner)
        if publication_date:
            self.match_field("dlhub.publication_date", publication_date)
        return self

    def match_authors(self, authors, match_all=True):
        """Add authors to the query.

        Args:
            authors (str or list of str): The authors to match.
            match_all (bool): If ``True``, will require all authors be on any results.
                    If ``False``, will only require one author to be in results.
                    **Default**: ``True``.

        Returns:
            DLHubSearchHelper: Self
        """
        if not authors:
            return self
        if isinstance(authors, str):
            authors = [authors]

        # TODO: Should we always generate creatorName when ingesting into Search or do it in SDK?
        # TODO: Potential issue: Entries without family and given name specific
        # TODO: Potential issue: Does not require first/lastname to be associated with same author
        for i, author in enumerate(authors):
            temp = author.split(",")

            # Family name is mandatory
            self.match_field(field="datacite.creators.familyName",
                             value='"{}"'.format(temp[0]), required=True if i == 0 else match_all,
                             new_group=True)

            # Given name is optional
            if len(temp) > 1:
                # If provided, it should be matched with the surname
                self.match_field(field="datacite.creators.givenName",
                                 value='"{}"'.format(temp[1].strip()), required=True,
                                 new_group=False)
        return self

    def match_domains(self, domains, match_all=True):
        """Add domains to the query.

        Args:
            domains (str or list of str): The domains to match.
            match_all (bool): If ``True``, will require all domains be on any results.
                    If ``False``, will only require one domain to be in results.
                    **Default**: ``True``.

        Returns:
            DLHubSearchHelper: Self
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

    def match_doi(self, doi):
        """Add a DOI to the query.

        Args:
            doi (str): The DOI to match.

        Returns:
            DLHubSearchHelper: Self
        """
        if doi:
            self.match_field("datacite.relatedIdentifiers.relatedIdentifier", '"{}"'.format(doi))
        return self


def filter_latest(results):
    """Get only the models with the most recent publication date

    Args:
        results ([dict]): List of results to filter
    Returns:
        [dict]: Only the most recent results
    """
    latest_res = {}

    # Loop over all results, get most recent publication for each servable
    for res in results:
        # TODO: Remove these warnings once search index is fixed
        if 'shorthand_name' not in res['dlhub']:
            warn('Found entries in DLHub index that lack shorthand_name. '
                 'Please contact DLHub team', RuntimeWarning)
            continue
        if 'publication_date' not in res['dlhub']:
            warn('Found entries in DLHub index that lack publication_date.'
                 ' Please contact DLHub team', RuntimeWarning)
            continue
        ident = res["dlhub"]["shorthand_name"]
        pub_date = int(res["dlhub"]["publication_date"])

        # If res not in latest_res, or res version is newer than latest_res
        # TODO: Make publication_date an integer in Search
        if latest_res.get(ident, ({}, -1))[1] < pub_date:
            latest_res[ident] = (res, pub_date)

    # Return only the most recent models
    return [r[0] for r in latest_res.values()]


def get_method_details(metadata, method_name=None):
    """Get the method details for use by humans

    Gets only the method fields out of the metadata record for an objecvt,
    removes the "method_details" field, which is used only during construction
    of the object.

    Will either return the data for all methods or, if ``method_name`` is provided,
    only a single function

    Args:
        metadata (dict): Metadata record for a servable
        method_name (str): Optional: Name of the function to retrieve
    Returns:
        dict: Metadata for the servable method, or a single method of ``method_name`` is used
    """

    # Get the "methods" block
    methods = metadata['servable']['methods']

    # Remove "method_details"
    for m in methods.values():
        m.pop('method_details', None)

    # If desired, return only a single method
    if method_name is not None:
        if method_name not in methods:
            raise ValueError('No such method: {}'.format(method_name))
        return methods[method_name]
    return methods
