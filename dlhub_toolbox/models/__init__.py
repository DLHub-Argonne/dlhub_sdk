from itertools import zip_longest
from datetime import datetime
from zipfile import ZipFile
import os

__dlhub_version__ = '0.1'


class BaseMetadataModel:
    """Base class for models describing objects published via DLHub

    Covers information that goes in the :code:`datacite` block of the metadata file and
    some of the DLHub block."""

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
        self.rights = []
        self.abstract = None
        self.methods = None
        self.domain = ''
        self.visible_to = ['public']
        self.doi = None
        self.publication_year = str(datetime.now().year)
        self.files = []
        self.dlhub_id = None

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
        self.version = str(version)
        return self

    def set_abstract(self, abstract):
        """Define an abstract for this artifact. Use for a high-level summary

        Args:
            abstract (string): Description of this artifact
        """
        self.abstract = abstract
        return self

    def set_methods(self, methods):
        """Define a methods section for this artifact. Use to describe any specific details
        about how the dataset, model, etc was generated.

        Args:
            methods (str): Detailed method descriptions
        """
        self.methods = methods
        return self

    def set_domain(self, domain):
        """Set the field of science that is associated with this artifcat

        Args:
            domain (string): Name of a field of science (e.g., "materials science")
        """
        self.domain = domain
        return self

    def set_visibility(self, visible_to):
        """Set the list of people this artifact should be visible to.

        By default, it will be visible to anyone (["public"]).

        Args:
            visible_to ([string]): List of allowed users and groups, listed by GlobusAuth UUID
        """
        self.visible_to = visible_to
        return self

    def set_doi(self, doi):
        """Set the DOI of this object, if available

        This function is only for advanced usage. Most users of the toolbox will not
        know the DOI before sending the doi in to DLHub.

        Args:
            doi (string): DOI of the object
        """
        self.doi = doi
        return self

    def set_dlhub_id(self, dlhub_id):
        """Set the identifier of this object

        This function is only for advanced users.

        Args:
            dlhub_id (string): UUID of artifact
        """
        self.dlhub_id = dlhub_id
        return self

    def set_publication_year(self, year):
        """Define the publication year

        This function is only for advanced usage. Normally, this will be assigned automatically

        Args:
            year (string): Publication year
        """

        self.publication_year = str(year)
        return self

    def add_rights(self, uri=None, rights=None):
        """Any rights information for this resource. Provide a rights management statement for the
        resource or reference a service providing such information. Include embargo information if
        applicable. Use the complete title of a license and include version information if applicable.

        Args:
            uri (string): URI of the rights
            rights (string): Description of the rights
        """

        if uri is None and rights is None:
            raise ValueError('You must defined either a URI or the rights')

        # Make the rights
        new_rights = {}
        if uri is not None:
            new_rights['rightsURI'] = uri
        if new_rights is not None:
            new_rights['rights'] = rights

        # Add it to the list
        self.rights.append(new_rights)
        return self

    def add_funding_reference(self, name, identifier=None, identifier_type=None,
                              award_number=None, award_title=None, award_uri=None):
        """Add a funding source to the list of resources

        Args:
            name (string): Name of funding provider
            identifier (string): Identifier (e.g., ISNI) of the funder
            identifier_type (string): Type of the identifier (ISNI, GRID, Crossref Funder ID, Other)
            award_number (string): Code assigned by the funder
            award_title (string): Title of the award
            award_uri (string): URI of the award
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
            funder['awardNumber'] = {'awardNumber': award_number}
            if award_uri is not None:
                funder['awardNumber']['awardURI'] = award_uri
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

    def add_files(self, files):
        """Add files that should be distributed with this artifact

        Args:
            files ([string]): Paths of files that should be published
        """

        # Type checking
        if isinstance(files, str):
            files = [files]

        self.files.extend(files)
        return self

    def to_dict(self):
        """Render the dataset to a JSON description

        Returns:
            (dict) A description of the dataset in a form suitable for download"""

        # Check for required fields
        if self.title is None:
            raise ValueError('Title must be specified. Use `set_title`')

        # Populate initial fields
        out = {"datacite": {
            "creators": self.authors,
            "titles": [{'title': self.title}],
            "publisher": "DLHub",
            "publicationYear": self.publication_year
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
        if len(self.rights) > 0:
            out['datacite']['rightsList'] = self.rights

        # Add in the DOI, if known. Use a fake DOI otherwise
        doi = self.doi
        if doi is None:
            doi = '10.YET/UNASSIGNED'
        out['datacite']['identifier'] = {'identifier': doi, 'identifierType': 'DOI'}

        # Add in descriptions
        desc = []
        if self.abstract is not None:
            desc.append({'description': self.abstract, 'descriptionType': 'Abstract'})
        if self.methods is not None:
            desc.append({'description': self.methods, 'descriptionType': 'Methods'})
        if len(desc) > 0:
            out['datacite']['descriptions'] = desc

        # Add in the DLHub block
        out['dlhub'] = {
            'version': __dlhub_version__,
            'domain': self.domain,
            'visible_to': self.visible_to,
            'id': self.dlhub_id
        }
        return out

    def list_files(self):
        """Provide a list of files associated with this dataset. This list
        should contain all of the files necessary to recreate the dataset.

        Returns:
            ([string]) list of file paths"""
        return self.files

    def get_zip_file(self, path):
        """Write all the listed files to a ZIP object

        Takes all of the files returned by `list_files`. First determines the largest common
        path of all files, and preserves directory structure by using this common path as the
        root directory. For example, if the files are "/home/a.pkl" and "/home/a/b.dat", the common
        directory is "/home" and the files will be stored in the Zip as "a.pkl" and "a/b.dat"

        Args:
            path (string): Path for the ZIP File
        Returns:
            (string): Base path for the ZIP file (useful for adjusting the paths of the files
                included in the metadata model)
        """

        # Open the zip file in "exclusively create" (x) mode
        with ZipFile(path, 'x') as newzip:
            # Get the files
            files = self.list_files()

            # Shortcut: if no files
            if len(files) == 0:
                return '.'

            # Get the directories for all the files
            directories = [f if os.path.isdir(f) else os.path.dirname(f) for f in files]

            # Get the largest common path
            common_path = os.path.commonpath(os.path.abspath(d) for d in directories)

            # Add each file to the directory
            for file in files:
                newzip.write(file, arcname=os.path.relpath(file, common_path))

            return common_path
