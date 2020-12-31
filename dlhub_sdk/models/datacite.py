from itertools import zip_longest

from pydantic import AnyUrl, BaseModel, Field
from typing import List, Optional, Sequence, Union
from enum import Enum


class DataciteIdentifier(BaseModel):
    """A persistent identifier that identifies a resource. Currently, only DOI is allowed."""
    class DataciteIdentifierType(str, Enum):
        DOI = "DOI"

    identifier: str = '10.datacite/placeholder'
    identifierType: DataciteIdentifierType = DataciteIdentifierType.DOI


class DataciteCreator(BaseModel):
    """A researcher involved working on the data, or the authors of the publication in priority order.

    May be a corporate/institutional or personal name. Format: Family, Given"""

    class NameIdentifier(BaseModel):
        nameIdentifier: str
        nameIdentifierScheme: str
        schemeURI: Optional[AnyUrl]

    creatorName: Optional[str] = None
    nameIdentifiers: List[NameIdentifier] = Field(default_factory=list)
    affiliations: Optional[List[str]] = Field(default_factory=list)
    familyName: Optional[str] = None
    givenName: Optional[str] = None

    @classmethod
    def from_name(cls, name: str, affiliations: Optional[Sequence[str]]) -> 'DataciteCreator':
        """Create a Creator from a string in format "familyName, givenName"

        Args:
            name: Name of the creator
            affiliations: List of affiliations of the creator
        Returns:
            A DataciteCreator object
        """

        family_name, given_name = name.split(",", 1)
        return DataciteCreator(familyName=family_name.strip(), givenName=given_name.strip(),
                               affiliations=affiliations)


class DataciteTitle(BaseModel):
    class DataciteTitleType(Enum):
        AlternativeTitle = "AlternativeTitle"
        Subtitle = "Subtitle"
        TranslatedTitle = "TranslatedTitle"
        Other = "Other"

    title: str = Field(...)
    type: Optional[DataciteTitleType]
    lang: Optional[str]


class DataciteSubject(BaseModel):
    subject: str = ""
    subjectScheme: Optional[str] = ""
    schemeURI: Optional[AnyUrl] = ""
    valueURI: Optional[AnyUrl] = ""
    lang: str = ""


class DataciteResourceTypeGeneral(Enum):
    Audiovisual = "Audiovisual"
    Collection = "Collection"
    Dataset = "Dataset"
    Event = "Event"
    Image = "Image"
    InteractiveResource = "InteractiveResource"
    Model = "Model"
    PhysicalObject = "PhysicalObject"
    Service = "Service"
    Software = "Software"
    Sound = "Sound"
    Text = "Text"
    Workflow = "Workflow"
    Other = "Other"


class DataciteResourceType(BaseModel):
    resourceType: Optional[str] = ""
    resourceTypeGeneral: DataciteResourceTypeGeneral = None


class DataciteContributor(BaseModel):
    class DataciteContributorType(Enum):
        ContactPerson = "ContactPerson"
        DataCollector = "DataCollector"
        DataCurator = "DataCurator"
        DataManager = "DataManager"
        Editor = "Editor"
        HostingInstitution = "HostingInstitution"
        Other = "Other"
        Producer = "Producer"
        ProjectLeader = "ProjectLeader"
        ProjectManager = "ProjectManager"
        ProjectMember = "ProjectMember"
        RegistrationAgency = "RegistrationAgency"
        RegistrationAuthority = "RegistrationAuthority"
        RelatedPerson = "RelatedPerson"
        ResearchGroup = "ResearchGroup"
        RightsHolder = "RightsHolder"
        Researcher = "Researcher"
        Sponsor = "Sponsor"
        Supervisor = "Supervisor"
        WorkPackageLeader = "WorkPackageLeader"

    contributorType: DataciteContributorType = None
    contributorName: str = ""
    affiliations: Optional[List[str]] = Field(default_factory=list)
    familyName: Optional[str] = None
    givenName: Optional[str] = None


class DataciteAlternateIdentifier(BaseModel):
    """An identifier or identifiers other than the primary Identifier applied to the resource being registered.

     This may be any alphanumeric string which is unique within its domain of issue. May be used for local identifiers.
    AlternateIdentifier should be used for another identifier of the same instance (same location, same file)."""

    alternateIdentifier: str
    alternateIdentifierType: str


class DataciteRelatedIdentifierType(Enum):
    """Types of identifiers for different objects"""
    ARK = "ARK"
    arXiv = "arXiv"
    bibcode = "bibcode"
    DOI = "DOI"
    EAN13 = "EAN13"
    EISSN = "EISSN"
    Handle = "Handle"
    IGSN = "IGSN"
    ISBN = "ISBN"
    ISSN = "ISSN"
    ISTC = "ISTC"
    LISSN = "LISSN"
    LSID = "LSID"
    PMID = "PMID"
    PURL = "PURL"
    UPC = "UPC"
    URL = "URL"
    URN = "URN"


class DataciteRelationType(Enum):
    """Ways another object is related to the object describe by our DataCite record"""
    IsCitedBy = "IsCitedBy"
    Cites = "Cites"
    IsSupplementTo = "IsSupplementTo"
    IsSupplementedBy = "IsSupplementedBy"
    IsContinuedBy = "IsContinuedBy"
    Continues = "Continues"
    IsNewVersionOf = "IsNewVersionOf"
    IsPreviousVersionOf = "IsPreviousVersionOf"
    IsPartOf = "IsPartOf"
    HasPart = "HasPart"
    IsReferencedBy = "IsReferencedBy"
    References = "References"
    IsDocumentedBy = "IsDocumentedBy"
    Documents = "Documents"
    IsCompiledBy = "IsCompiledBy"
    Compiles = "Compiles"
    IsVariantFormOf = "IsVariantFormOf"
    IsOriginalFormOf = "IsOriginalFormOf"
    IsIdenticalTo = "IsIdenticalTo"
    HasMetadata = "HasMetadata"
    IsMetadataFor = "IsMetadataFor"
    Reviews = "Reviews"
    IsReviewedBy = "IsReviewedBy"
    IsDerivedFrom = "IsDerivedFrom"
    IsSourceOf = "IsSourceOf"


class DataciteRelatedIdentifier(BaseModel):
    """Identifier of a related resource. Use this property to indicate subsets of properties, as appropriate."""
    relatedIdentifier: str
    relatedIdentifierType: DataciteRelatedIdentifierType
    relatedMetadataScheme: str
    schemeURI: Optional[AnyUrl] = None


class DataciteDescription(BaseModel):
    """Additional information that does not fit in any of the other categories.

    May be used for technical information. It is a best practice to supply a description."""

    class DataciteDescriptionType(Enum):
        abstract = "Abstract"
        methods = "Methods"
        seriesInformation = "SeriesInformation"
        tableOfContents = "TableOfContents"
        technicalInfo = "TechnicalInfo"
        other = "Other"

    descriptionType: DataciteDescriptionType
    description: str


class DataciteRights(BaseModel):
    """"Any rights information for this resource. Provide a rights management statement for the resource or reference
     a service providing such information. Include embargo information if applicable. Use the complete title of a
     license and include version information if applicable."""

    rightsURI: Optional[str] = None
    rights: Optional[str] = None


class DataciteFundingReference(BaseModel):
    """Information about financial support (funding) for the resource being registered."""

    class FunderIdentifier(BaseModel):
        """Uniquely identifies a funding entity, according to various types."""

        class FunderIdentifierType(Enum):
            ISNI = "ISNI"
            GRID = "GRID"
            CrossRef = "Crossref Funder ID"
            Other = "Other"

        funderIdentifier: str
        funderIdentifierType: FunderIdentifierType

    class AwardNumber(BaseModel):
        awardNumber: str
        awardURI: Optional[AnyUrl] = None

    funderName: str
    funderIdentifier: Optional[FunderIdentifier] = None
    awardNumber: Optional[AwardNumber] = None
    awardTitle: Optional[str] = None


class Datacite(BaseModel):
    identifier: DataciteIdentifier = Field(default_factory=DataciteIdentifier)
    creators: List[DataciteCreator] = Field(default_factory=list)
    titles: List[DataciteTitle] = Field(default_factory=list)
    publisher: str = "DLHub"
    publicationYear: str = ""
    subjects: List[DataciteSubject] = Field(default_factory=list)
    resourceType: Optional[DataciteResourceType] = None
    contributors: List[DataciteContributor] = Field(default_factory=list)
    descriptions: List[DataciteDescription] = Field(default_factory=list)
    language: Optional[str] = None
    alternateIdentifiers: List[DataciteAlternateIdentifier] = Field(default_factory=list)
    relatedIdentifiers: List[DataciteRelatedIdentifier] = Field(default_factory=list)
    rightsList: List[DataciteRights] = Field(default_factory=list)
    fundingReferences: List[DataciteFundingReference] = Field(default_factory=list)
    version: Optional[str] = None

    __datacite_version: Optional[str] = "4.3"

    def set_title(self, title: str) -> 'Datacite':
        """Set the title for the artefact

        Use this method if you only have one title for the object

        Args:
            title - Desired title
        """
        self.titles = [DataciteTitle(title=title)]
        return self

    def set_creators(self, authors: List[str], affiliations: List[Sequence[str]] = ()) -> 'Datacite':
        """Add authors to an object

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
            self.creators.append(DataciteCreator(
                givenName=given,
                familyName=family,
                affiliations=aff
            ))
        return self

    def set_abstract(self, abstract: str):
        """Define an abstract for this object

        Args:
            abstract: Text of abstract
        """

        abs_block = DataciteDescription(description=abstract, descriptionType='Abstract')
        self._add_or_replace_description(abs_block)
        return self

    def _add_or_replace_description(self, block: DataciteDescription):
        """Add a description or replace the text of an existing description of the same type

        Ensures no more than one of a certain type exists in the descriptions list

        Args:
            block: Description text and type block
        """
        # Delete block of same type if it already exists
        self.descriptions = [
            x for x in self.descriptions
            if x.descriptionType != block.descriptionType
        ]
        # Add the new block
        self.descriptions.append(block)

    def set_methods(self, methods: str):
        """Define the methods used to create this object

        Args:
            methods: Text of methods section
        """
        block = DataciteDescription(description=methods, descriptionType='Methods')
        self._add_or_replace_description(block)
        return self

    def set_identifier(self, doi: str) -> 'Datacite':
        """Set the identifier for this object

        Args:
            doi: Identifier for the object. Must be a DOI
        """
        self.identifier = DataciteIdentifier(identifier=doi)
        return self

    def add_rights(self, uri: Optional[str] = None, rights: Optional[str] = None) -> 'Datacite':
        """Any rights information for this resource. Provide a rights management statement for the
        resource or reference a service providing such information. Include embargo information if
        applicable. Use the complete title of a license and include
        version information if applicable.

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
        self.rightsList.append(DataciteRights(**new_rights))
        return self

    def add_funding_reference(self, name: str, identifier: Optional[str] = None,
                              identifier_type: Optional[str] = None,
                              award_number: Optional[str] = None,
                              award_title: Optional[str] = None,
                              award_uri: Optional[str] = None) -> 'Datacite':
        """Add a funding source to the list of resources

        Args:
            name: Name of funding provider
            identifier: Identifier (e.g., ISNI) of the funder
            identifier_type (string): Type of the identifier (ISNI, GRID, Crossref Funder ID, Other)
            award_number (string): Code assigned by the funder
            award_title (string): Title of the award
            award_uri (string): URI of the award
        """

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
        self.fundingReferences.append(DataciteFundingReference(**funder))
        return self

    def add_alternate_identifier(self, identifier: str, identifier_type: str) -> 'Datacite':
        """Add an identifier of this object in another service

        Args:
            identifier (string): Identifier
            identifier_type (string): Identifier type
        """

        self.alternateIdentifiers.append(DataciteAlternateIdentifier(
            alternateIdentifier=identifier,
            alternateIdentifierType=identifier_type
        ))
        return self

    def add_related_identifier(self, identifier: str, identifier_type: Union[str, DataciteRelatedIdentifierType],
                               relation_type: Union[str, DataciteRelationType]) -> 'Datacite':
        """Add an identifier of an artifact that is related to this resource (e.g., a paper
        that describes a dataset).

        You must define both the identifier and how it relates to this resource. The possible types
        of relations are listed in the
        `documentation for datacite
        <https://schema.datacite.org/meta/kernel-4.1/doc/DataCite-MetadataKernel_v4.1.pdf>_`
        on Page 25.

        Args:
            identifier: Identifier
            identifier_type: Identifier type
            relation_type: Relation between this identifier and the object you are describing
        """

        self.relatedIdentifiers.append(DataciteRelatedIdentifier(
            relatedIdentifier=identifier,
            relatedIdentifierType=identifier_type,
            relationType=relation_type
        ))
        return self

    def to_json(self, exclude_unset: bool = True) -> str:
        return self.json(exclude_unset=exclude_unset)

    def to_xml(self):
        raise NotImplementedError()

    def describe(self) -> str:
        return "Datacite version: {}".format(self.__datacite_version)

    @classmethod
    def from_codemeta(cls, metadata: dict) -> 'Datacite':
        """Generate Datacite metadata from a Codemeta

        Args:
            metadata: Codemeta-format metadata
        Returns:
            Datacite metadata object
        """

        # Taken from: https://github.com/caltechlibrary/ames/blob
        #             /920c028f7fcceaa1baf3a645a37de587dd2dbc41/matchers/caltechdata.py#L61

        datacite = {}
        if 'author' in metadata:
            creators = []
            for a in metadata['author']:
                cre = {}
                cre['creatorName'] = a['familyName'] + ', ' + a['givenName']
                cre['familyName'] = a['familyName']
                cre['givenName'] = a['givenName']
                if '@id' in a:
                    idv = a['@id']
                    split = idv.split('/')
                    idn = split[-1]
                    cre['nameIdentifiers'] = [{
                        'nameIdentifier': idn, 'nameIdentifierScheme': 'ORCID',
                        'schemeURI': 'http://orcid.org'}]
                    # Should check for type and remove hard code URI
                if 'affiliation' in a:
                    cre['affiliations'] = [a['affiliation']]
                    # Should check if can support multiple affiliations
                creators.append(cre)
            datacite['creators'] = creators
        if 'name' in metadata:
            datacite['titles'] = [{'title': metadata['name']}]
        if 'license' in metadata:
            # Assuming uri to name conversion, not optimal
            uri = metadata['license']
            name = uri.split('/')[-1]
            datacite['rightsList'] = [{'rights': name, 'rightsURI': uri}]
        if 'keywords' in metadata:
            sub = []
            for k in metadata['keywords']:
                sub.append({"subject": k})
            datacite['subjects'] = sub
        if 'funder' in metadata:
            # Kind of brittle due to limitations in codemeta
            fund_list = []
            grant_info = ''
            if 'funding' in metadata:
                grant_info = metadata['funding'].split(',')
            if isinstance(metadata['funder'], list):
                count = 0
                for funder in metadata['funder']:
                    entry = {'funderName': funder['name']}
                    if '@id' in funder:
                        element = {}
                        element['funderIdentifier'] = funder['@id']
                        element['funderIdentifierType'] = 'Crossref Funder ID'
                        entry['funderIdentifier'] = element
                    if grant_info != '':
                        split = grant_info[count].split(';')
                        entry['awardNumber'] = {'awardNumber': split[0]}
                        if len(split) > 1:
                            entry['awardTitle'] = split[1]
                    count = count + 1
            else:
                funder = metadata['funder']
                entry = {'funderName': funder['name']}
                if '@id' in funder:
                    element = {}
                    element['funderIdentifier'] = funder['@id']
                    element['funderIdentifierType'] = 'Crossref Funder ID'
                    entry['funderIdentifier'] = element
                if grant_info != '':
                    split = grant_info[0].split(';')
                    entry['awardNumber'] = {'awardNumber': split[0]}
                    if len(split) > 1:
                        entry['awardTitle'] = split[1]
                fund_list.append(entry)

            datacite['fundingReferences'] = fund_list
        return Datacite.parse_obj(datacite)
