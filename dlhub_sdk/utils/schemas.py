"""Utilities for validating against DLHub schemas"""
from jsonschema import Draft7Validator, RefResolver
import requests

_schema_repo = "https://raw.githubusercontent.com/DLHub-Argonne/dlhub_schemas/master/schemas/"


def validate_against_dlhub_schema(document, schema_name):
    """Validate a metadata document against one of the DLHub schemas

    Note: Requires an internet connection

    Args:
        document (dict): Document instance to be validated
        schema_name (string): Name of schema (e.g., "dataset" for validating datasets).
            For full list, see: https://github.com/DLHub-Argonne/dlhub_schemas
    Raises:
        (jsonschema.SchemaError) If the schema fails to validate
    """

    # Make the schema validator
    schema = requests.get("{}/{}.json".format(_schema_repo, schema_name)).json()
    validator = Draft7Validator(schema, resolver=RefResolver(_schema_repo, schema))

    # Test the document
    validator.validate(document)


def codemeta_to_datacite(metadata):
    """Generate datacite from codemeta metadata

    Args:
        metadata (dict): Codemeta metadata
    Returns:
        (dict) datacite-compatabile metadata
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
    return datacite
