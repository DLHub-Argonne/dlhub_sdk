"""Utility classes for interacting with the DLHub Search Index"""

from mdf_toolbox.search_helper import SearchHelper


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
        return methods[method_name]
    return methods


class DLHubSearchHelper(SearchHelper):
    """Helper class for building queries with DLHub"""

    def __init__(self, search_client):
        super(DLHubSearchHelper, self).__init__("dlhub", search_client=search_client)

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
                    **Default**: ``True``.

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

    def match_doi(self, doi):
        """Add a DOI to the query.

        Args:
            doi (str): The DOI to match.

        Returns:
            DLHubClient: Self
        """
        if doi:
            self.match_field("datacite.doi", doi)
        return self
