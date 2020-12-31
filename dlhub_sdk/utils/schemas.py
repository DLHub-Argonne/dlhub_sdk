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
