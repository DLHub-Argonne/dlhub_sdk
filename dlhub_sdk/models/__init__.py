from itertools import zip_longest
from datetime import datetime
from six import string_types
from zipfile import ZipFile
from glob import glob
import json
import uuid
import sys
import os
import re

from dlhub_sdk.version import __version__
from dlhub_sdk.utils.schemas import codemeta_to_datacite

name_re = re.compile(r'^\S+$')


class BaseMetadataModel:
    """Base class for models describing objects published via DLHub

    Covers information that goes in the :code:`datacite` block of the metadata file and
    some of the DLHub block.

    ## Using a MetadataModel

    There are many kinds of MetadataModel classes that each describe a different kind of object.
    Each of these different types are created using the :code:`create_model` operation
    (e.g., :code:`KerasModel.create_model('model.h5')`), but have different arguments depending
    on the type of object. For example, TensorFlow models only require the directory created
    when saving the model for serving but scikit-learn models require the pickle file, how
    the pickle was created (e.g., with joblib), and how many input features it requires.

    Once created, you will need to fill in additional details about the object to make it reusable.
    The MetadataModel classes attempt to learn as much about an object as possible automatically,
    but there is some information that must be provided by a human. To start, you must define a
    title and name for the object and are encouraged to provide an abstract describing the model
    and list any associated papers/websites that describe the model. You will fill plenty of
    examples for how to describe the models in the DLHub_containers repostiory. Some types of
    objects require data specific to their type (e.g., Python servables need a list of required
    packages). We encourage you to find examples for your specific type of object in the containers
    repository for inspiration and to see the Python documentation for each Metadata Model.

    The MetadataModel object can be saved using the `to_dict` operation and read back into
    memory using the `from_dict` method. We recommend you save your dictionary to disk in the
    JSON or yaml format, which will allow for manual edits to be made before submitting or
    resubmitting a object description.
    """

    def __init__(self):
        """
        Initialize a dataset record
        """

        # Populate initial fields
        self._output = {"datacite": {
            "creators": [],
            "titles": [{'title': None}],
            "publisher": "DLHub",
            "publicationYear": str(datetime.now().year),
            "identifier": {'identifier': '10.YET/UNASSIGNED', 'identifierType': 'DOI'},
            "descriptions": [],
            "fundingReferences": [],
            "relatedIdentifiers": [],
            "alternateIdentifiers": [],
            "rightsList": []
        }, "dlhub": {
            "version": __version__,
            "domains": [],
            "visible_to": ["public"],
            'id': None,
            'name': None,
            'files': {}
        }}

    def __getitem__(self, item):
        return self._output[item]

    @classmethod
    def create_model(cls, **kwargs):
        """Instantiate the metadata model.

        Takes in arguments that allow metadata describing a dataset to be autogenerated. For
        example, these could include options describing how to read a dataset from a CSV file or
        which class method to invoke on a Python pickle object.
        """
        
        return cls()

    def read_codemeta_file(self, directory=None):
        """Read in metadata from a codemeta.json file

        Args:
            directory (string): Path to directory contain the codemeta.json file
                (default: current working directory)
        """

        # If no directory, use the current
        if directory is None:
            directory = os.getcwd()

        # Load in the codemeta
        with open(os.path.join(directory, 'codemeta.json')) as fp:
            codemeta = json.load(fp)

        # Convert it to datacite and store it
        datacite = codemeta_to_datacite(codemeta)
        self._output["datacite"].update(datacite)

        return self

    def set_authors(self, authors, affiliations=list()):
        """Add authors to a dataset

        Args:
            authors ([string]): List of authors for the dataset.
                In format: "<Family Name>, <Given Name>"
            affiliations ([[string]]): List of affiliations for each author.
        """
        for author, aff in zip_longest(authors, affiliations, fillvalue=[]):
            # Get the authors
            temp = author.split(",")
            family = temp[0].strip()
            given = temp[1].strip()

            # Add them to the list
            self._output["datacite"]["creators"].append({
                "givenName": given,
                "familyName": family,
                "affiliations": aff,
            })
        return self

    def set_title(self, title):
        """Add a title to the dataset"""
        self._output["datacite"]["titles"][0]["title"] = title
        return self

    def set_version(self, version):
        """Set the version of this resource

        Args:
            version (string): Version number
        """
        self._output["datacite"]["version"] = str(version)
        return self

    def set_abstract(self, abstract):
        """Define an abstract for this artifact. Use for a high-level summary

        Args:
            abstract (string): Description of this artifact
        """
        abs_block = {'description': abstract, 'descriptionType': 'Abstract'}

        # Delete Abstract block if it already exists
        self._output["datacite"]["descriptions"] = [
            x for x in self._output["datacite"]["descriptions"]
            if x["descriptionType"] != "Abstract"
        ]

        # Add the new block
        self._output["datacite"]["descriptions"].append(abs_block)
        return self

    def set_methods(self, methods):
        """Define a methods section for this artifact. Use to describe any specific details
        about how the dataset, model, etc was generated.

        Args:
            methods (str): Detailed method descriptions
        """
        method_blcok = {'description': methods, 'descriptionType': 'Methods'}

        # Delete Methods block if it already exists
        self._output["datacite"]["descriptions"] = [
            x for x in self._output["datacite"]["descriptions"]
            if x["descriptionType"] != "Methods"
        ]

        self._output["datacite"]["descriptions"].append(method_blcok)
        return self

    def set_domains(self, domains):
        """Set the field of science that is associated with this artifcat

        Args:
            domains ([string]): Name of a fields of science (e.g., "materials science")
        """
        self._output["dlhub"]["domains"] = domains
        return self

    def set_visibility(self, visible_to):
        """Set the list of people this artifact should be visible to.

        By default, it will be visible to anyone (["public"]).

        Args:
            visible_to ([string]): List of allowed users and groups, listed by GlobusAuth UUID
        """
        self._output["dlhub"]["visible_to"] = visible_to
        return self

    def set_doi(self, doi):
        """Set the DOI of this object, if available

        This function is only for advanced usage. Most users of the toolbox will not
        know the DOI before sending the doi in to DLHub.

        Args:
            doi (string): DOI of the object
        """
        self._output["datacite"]["identifier"]["identifier"] = doi
        return self

    def set_dlhub_id(self, dlhub_id):
        """Set the identifier of this object

        This function is only for advanced users.

        Args:
            dlhub_id (string): UUID of artifact
        """
        self._output["dlhub"]["id"] = dlhub_id
        return self

    def assign_dlhub_id(self):
        """Assign the step a DLHub id

        Generates a UUID, which is guaranteed to be unique
        """

        return self.set_dlhub_id(str(uuid.uuid1()))

    @property
    def dlhub_id(self):
        return self._output["dlhub"]["id"]

    def set_name(self, name):
        """Set the name of artifact.

        Should be something short, descriptive, and memorable

        Args:
            name (string): Name of artifact
        """
        if name_re.match(name) is None:
            raise ValueError('Name cannot contain any whitespace')
        self._output["dlhub"]["name"] = name
        return self

    def set_publication_year(self, year):
        """Define the publication year

        This function is only for advanced usage. Normally, this will be assigned automatically

        Args:
            year (string): Publication year
        """
        self._output["datacite"]["publicationYear"] = str(year)
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
        self._output["datacite"]["rightsList"].append(new_rights)
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
        self._output["datacite"]["fundingReferences"].append(funder)

        return self

    def add_alternate_identifier(self, identifier, identifier_type):
        """Add an identifier of this artifact in another service

        Args:
            identifier (string): Identifier
            identifier_type (string): Identifier type
        """

        self._output["datacite"]["alternateIdentifiers"].append({
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

        self._output["datacite"]["relatedIdentifiers"].append({
            'relatedIdentifier': identifier,
            'relatedIdentifierType': identifier_type,
            'relationType': relation_type
        })
        return self

    def add_file(self, file, name=None):
        """Add a file to the list of files to be distributed with the artifact

        Args:
            file (string): Path to the file
            name (string): Optional. Name of the file, if it is a file that serves a specific
                purpose in software based on this artifact (e.g., if this is a pickle file
                of a scikit-learn model)
        """

        if name is None or name == "other":
            if "other" not in self._output["dlhub"]["files"]:
                self._output["dlhub"]["files"]["other"] = []
            self._output["dlhub"]["files"]['other'].append(file)
        else:
            self._output["dlhub"]["files"][name] = file
        return self

    def add_directory(self, directory, recursive=False):
        """Add all the files in a directory

        Args:
            directory (string): Path to a directory
            recursive (bool): Whether to add all files in a directory
        """

        # Get potential files
        if recursive:
            if sys.version_info < (3, 5):
                raise RuntimeError('You must use Python >= 3.5 to do recursive listing')
            hits = glob('{}/**/*'.format(directory), recursive=True)
        else:
            hits = glob('{}/*'.format(directory))

        # Get only the files
        files = [x for x in hits if os.path.isfile(x)]
        return self.add_files(files)

    def add_files(self, files):
        """Add files that should be distributed with this artifact.

        Args:
            files ([string]): Paths of files that should be published
        """

        # Type checking
        if isinstance(files, str):
            files = [files]

        # Add the files
        for file in files:
            self.add_file(file)
        return self

    def to_dict(self, simplify_paths=False, save_class_data=False):
        """Render the dataset to a JSON description

        Args:
            simplify_paths (bool): Whether to simplify the paths of each file
            save_class_data (bool): Whether to save data about the class
        Returns:
            (dict) A description of the dataset in a form suitable for download
        """

        # Check for required fields
        if self._output["datacite"]["titles"][0]["title"] is None:
            raise ValueError('Title must be specified. Use `set_title`')
        if self._output["dlhub"]["name"] is None:
            raise ValueError('Name must be specified. Use `set_name`')

        # Make a copy of the output
        out = dict(self._output)

        # Add the name of the class to the output, if desired
        if save_class_data:
            out['@class'] = '{}.{}'.format(self.__class__.__module__,
                                           self.__class__.__name__)

        # Prepare the files
        if simplify_paths:
            # Get the common path
            common_path = self._get_common_path()

            files = {}
            for k, v in out["dlhub"]["files"].items():
                if k == "other":
                    files[k] = [os.path.relpath(f, common_path) for f in v]
                else:
                    files[k] = os.path.relpath(v, common_path)

            # Copy over the current files list
            out["dlhub"]["files"] = files

        return out

    @classmethod
    def from_dict(cls, data):
        """Reconstitute class from dictionary

        Args:
            data (dict): Metadata for this class
        """

        # Create the object, overwrite data
        output = cls()
        output._output = dict(data)

        # Make sure the class information is removed
        if '@class' in output._output:
            del output._output['@class']

        return output

    def list_files(self):
        """Provide a list of files associated with this artifact.

        Returns:
            ([string]) list of file paths"""
        # Gather a list of all the files
        output = []
        for k, v in self._output["dlhub"]["files"].items():
            if isinstance(v, string_types):
                output.append(v)
            else:  # It is a list
                output.extend(v)
        return output

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
            if len(self.list_files()) == 0:
                return "."

            # Get the common path of all files
            root_path = self._get_common_path()

            # Add each file to the directory
            for file in self.list_files():
                newzip.write(file, arcname=os.path.relpath(file, root_path))

            return root_path

    def _get_common_path(self):
        """Determine the common path of all files

        Returns:
            (string) Common path
        """
        # Get the files
        files = self.list_files()

        # Shortcut: if no files
        if len(files) == 0:
            return '.'

        # Get the directories for all the files
        directories = [f if os.path.isdir(f) else os.path.dirname(f) for f in files]

        # Get the largest common path
        return os.path.commonpath(os.path.abspath(d) for d in directories)
