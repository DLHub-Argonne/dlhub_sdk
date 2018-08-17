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
        self.version = None
        self.funders = []
        self.alternate_ident = []
        self.related_ident = []

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

    def set_version(self, version):
        """Set the version of this resource

        Args:
            version (string): Version number
        """
        self.version = version
        return self

    def add_funding_reference(self, name, identifier=None, identifier_type=None,
                              award_number=None, award_title=None):
        """Add a funding source to the list of resources

        Args:
            name (string): Name of funding provider
            identifier (string): Identifier (e.g., ISNI) of the funder
            identifier_type (string): Type of the identifier (ISNI, GRID, Crossref Funder ID, Other)
            award_number (string): Code assigned by the funder
            award_title (string): Title of the award
        """

        # Error checking
        if identifier_type is None and identifier_type is not None:
            raise ValueError('Identifier type must be provided. "Other" is an option')
        if identifier_type not in ['ISNI', 'GRID', 'Crossref Funder ID', 'Other']:
            raise ValueError('Identifier type not recognized')

        # Format in datacite format
        funder = {'funderName': name}
        if identifier is not None:
            funder['funderIdentifier'] = {'funderIdentifier': identifier,
                                          'funderIdentifierType': identifier_type}
        if award_number is not None:
            funder['awardNumber'] = award_number
        if award_title is not None:
            funder['awardTitle'] = award_title

        # Append to the total list
        self.funders.append(funder)

        return self

    def add_alternate_identifier(self, identifier, identifier_type):
        """Add an identifier of this artifact in another service

        Args:
            identifier (string): Identifier
            identifier_type (string): Identifier type
        """

        self.alternate_ident.append({
            'alternateIdentifier': identifier,
            'alternateIdentifierType': identifier_type
        })
        return self

    def add_related_identifier(self, identifier, identifier_type, relation_type):
        """Add an identifier of an artifact that is related to this resource (e.g., a paper
        that describes a dataset).

        You must define both the identifier and how it relates to this resource. The possible types
        of relations are listed in the `documentaiton for datacite <https://schema.datacite.org/meta/kernel-4.1/doc/DataCite-MetadataKernel_v4.1.pdf>_`
        on Page 25. The most common one used in DLHub will likely be:

            - "IsDescribedBy": For a paper that describes a dataset or model
            - "IsDocumentedBy": For the software documentation for a model
            - "IsDerviedFrom": For the database a training set was pulled from

        Args:
            identifier (string): Identifier
            identifier_type (string): Identifier type
            relation_type (string): Relation between
        """

        if identifier_type not in ["ARK", "arXiv", "bibcode", "DOI", "EAN13", "EISSN", "Handle",
                                   "IGSN", "ISBN", "ISSN", "ISTC", "LISSN", "LSID", "PMID",
                                   "PURL", "UPC", "URL", "URN"]:
            raise ValueError('Unknown identifier type ({}).'.format(identifier_type))
        if relation_type not in ["IsCitedBy", "Cites", "IsSupplementTo", "IsSupplementedBy",
                                 "IsContinuedBy", "Continues", "IsNewVersionOf",
                                 "IsPreviousVersionOf", "IsPartOf", "HasPart", "IsReferencedBy",
                                 "References", "IsDocumentedBy", "Documents", "IsCompiledBy",
                                 "Compiles", "IsVariantFormOf", "IsOriginalFormOf",
                                 "IsIdenticalTo", "HasMetadata", "IsMetadataFor", "Reviews",
                                 "IsReviewedBy", "IsDerivedFrom", "IsSourceOf", "IsDescribedBy",
                                 "Describes"]:
            raise ValueError('Unknown relation type: ({})'.format(relation_type))

        self.related_ident.append({
            'relatedIdentifier': identifier,
            'relatedIdentifierType': identifier_type,
            'relationType': relation_type
        })
        return self

    def to_dict(self):
        """Render the dataset to a JSON description

        Returns:
            (dict) A description of the dataset in a form suitable for download"""
        out = {"datacite": {
            "creators": self.authors,
            "titles": [self.title],
            "publisher": "DLHub",
        }}

        # Add optional fields
        if self.version is not None:
            out['datacite']['version'] = self.version
        if len(self.funders) > 0:
            out['datacite']['fundingReferences'] = self.funders
        if len(self.related_ident):
            out['datacite']['relatedIdentifiers'] = self.related_ident
        if len(self.alternate_ident):
            out['datacite']['alternateIdentifiers'] = self.alternate_ident

        return out

    def list_files(self):
        """Provide a list of files associated with this dataset. This list
        should contain all of the files necessary to recreate the dataset.

        Returns:
            ([string]) list of file paths"""
        raise NotImplementedError()
