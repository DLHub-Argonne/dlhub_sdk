from itertools import zip_longest


class Dataset:

    def __init__(self):
        """
        Initialize a dataset record
        """

        self.authors = []
        self.title = None

    def set_authors(self, authors, affiliations=[]):
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
        """Render the dataset to a JSON description"""
        return {"datacite": {"creators": self.authors, "title": self.title}}
