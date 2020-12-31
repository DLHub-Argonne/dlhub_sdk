"""Tests for the datacite schema"""

import json
import os

from pytest import fixture

from dlhub_sdk.models.datacite import Datacite, DataciteCreator


@fixture()
def dc() -> Datacite:
    """An empty schema"""
    return Datacite()


@fixture()
def codemeta() -> dict:
    with open(os.path.join(os.path.dirname(__file__), "codemeta.json")) as fp:
        return json.load(fp)


def test_set_title(dc):
    dc.set_title("Test")
    assert dc.titles[0].title == "Test"


def test_set_authors(dc):
    dc.set_creators(["Ward, Logan"], [["Argonne National Laboratory"]])
    assert len(dc.creators) == 1
    assert dc.creators[0].givenName == "Logan"

    # Add a second author
    dc.creators.append(DataciteCreator.from_name("Blaiszik, Ben", ["University of Chicago"]))
    assert dc.creators[-1].affiliations == ["University of Chicago"]


def test_set_abstract(dc):
    dc.set_abstract("Test abstract")

    assert len(dc.descriptions) == 1
    assert dc.descriptions[0].description == "Test abstract"
    assert dc.descriptions[0].descriptionType.value == "Abstract"

    # Set a new value for the abstract
    dc.set_abstract("Second")

    assert len(dc.descriptions) == 1
    assert dc.descriptions[0].description == "Second"


def test_methods(dc):
    dc.set_methods("Test")

    assert len(dc.descriptions) == 1
    assert dc.descriptions[0].description == "Test"
    assert dc.descriptions[0].descriptionType.value == "Methods"

    # Make sure there is no collision between methods and abstract
    dc.set_abstract("Abstract")
    assert len(dc.descriptions) == 2


def test_rights(dc):
    dc.add_rights(rights="test")

    assert len(dc.rightsList) == 1
    assert dc.rightsList[0].rights == "test"


def test_funding(dc):
    dc.add_funding_reference("DOE", award_number="Fake", award_title="Fake award")

    assert len(dc.fundingReferences) == 1
    assert dc.fundingReferences[0].awardTitle == "Fake award"


def test_alternate_identifier(dc):
    dc.add_alternate_identifier("notAId", "ID")

    assert len(dc.alternateIdentifiers) == 1
    assert dc.alternateIdentifiers[0].alternateIdentifier == "notAId"


def test_from_codemeta(codemeta):
    # Make sure it validates and we get the first creator correct, at least
    dc = Datacite.from_codemeta(codemeta)
    assert dc.creators[0].givenName == "Carl"
