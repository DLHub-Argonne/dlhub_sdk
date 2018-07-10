from itertools import zip_longest


class BaseMetadataModel:
    """Base class for models describing objects published via DLHub

    Covers information that goes in the :code:`datacite` block of the metadata file."""

    def __init__(self):
        """
        Initialize a dataset record
        """

        self.authors = []
        self.title = None

    def set_authors(self, authors, affiliations=list()):
        """Add authors to a dataset

        Args:
            authors ([string]): List of authors for the dataset.
                In format: "<Family Name>, <Given Name>"
            affiliations ([[string]]): List of affiliations for each author.
        """
        self.authors = []
        for author, aff in zip_longest(authors, affiliations, fillvalue=[]):
            # Get the authors
            temp = author.split(",")
            family = temp[0].strip()
            given = temp[1].strip()

            # Add them to the list
            self.authors.append({
                "givenName": given,
                "familyName": family,
                "affiliations": aff,
            })
        return self

    def set_title(self, title):
        """Add a title to the dataset"""
        self.title = title
        return self

    def to_dict(self):
        """Render the dataset to a JSON description

        Returns:
            (dict) A description of the dataset in a form suitable for download"""
        return {"datacite": {"creators": self.authors, "title": self.title}}

    def list_files(self):
        """Provide a list of files associated with this dataset. This list
        should contain all of the files necessary to recreate the dataset.

        Returns:
            ([string]) list of file paths"""
        raise NotImplementedError()
