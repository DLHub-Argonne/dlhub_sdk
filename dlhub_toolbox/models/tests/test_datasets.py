from dlhub_toolbox.models.datasets import Dataset, TabularDataset
from dlhub_toolbox.models import __dlhub_version__

from datetime import datetime
import unittest
import os

from dlhub_toolbox.utils.schemas import validate_against_dlhub_schema


_year = str(datetime.now().year)


class TestModels(unittest.TestCase):

    maxDiff = None

    def test_dataset(self):
        m = Dataset().set_authors(["Ward, Logan"], ["University of Chicago"])\
            .set_title("Example dataset").add_alternate_identifier("10.11", "DOI")\
            .add_related_identifier("10.11", "DOI", 'IsDescribedBy')\
            .add_funding_reference("ANL LDRD", '1', 'ISNI', '201801', 'DLHub', 'http://funding.uri')\
            .set_version(1)\
            .add_rights("https://www.gnu.org/licenses/gpl-3.0.en.html", "GPL v3.0")\
            .set_abstract("Abstract").set_methods("Methods")\
            .set_visibility(['public']).set_domain("materials science")
        self.assertEqual(m.to_dict(),
                         {"datacite":
                              {"creators": [{"givenName": "Logan", "familyName": "Ward",
                                             "affiliations": "University of Chicago"}],
                               "titles": [{'title': "Example dataset"}],
                               "publisher": 'DLHub',
                               "publicationYear": _year,
                               "version": '1',
                               "resourceType": {"resourceTypeGeneral": "Dataset"},
                               "descriptions": [{
                                   "description": "Abstract", "descriptionType": "Abstract"
                               }, {
                                   "description": "Methods", "descriptionType": "Methods"
                               }],
                               "fundingReferences": [{
                                   "awardNumber": {"awardNumber": "201801", "awardURI": "http://funding.uri"},
                                   "awardTitle": "DLHub",
                                   "funderIdentifier": {'funderIdentifier': '1',
                                                        'funderIdentifierType': 'ISNI'},
                                   "funderName": "ANL LDRD"
                               }],
                               "relatedIdentifiers": [{
                                   "relatedIdentifier": "10.11",
                                   "relatedIdentifierType": "DOI",
                                   "relationType": "IsDescribedBy"
                               }],
                               "alternateIdentifiers": [{
                                   "alternateIdentifier": "10.11",
                                   "alternateIdentifierType": "DOI"
                               }],
                               "rightsList": [{
                                   "rightsURI": "https://www.gnu.org/licenses/gpl-3.0.en.html",
                                   "rights": "GPL v3.0"
                               }],
                               'identifier': {'identifier': '10.YET/UNASSIGNED',
                                              'identifierType': 'DOI'},
                               },
                          "dlhub": {
                              "version": __dlhub_version__,
                              "visible_to": ["public"],
                              "domain": "materials science"
                          }})
        validate_against_dlhub_schema(m.to_dict(), "dataset")

    def test_tabular_dataset(self):
        data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'test.csv'))
        m = TabularDataset(data_path)
        self.assertEqual({'x': {'name': 'x', 'type': 'integer'},
                          'y': {'name': 'y', 'type': 'integer'}}, m.columns)

        # Add some nonsense
        m.set_title('Example dataset')
        m.mark_inputs(['x'])
        m.mark_labels(['y'])
        m.annotate_column('x', description='Input variable', units='cm')
        m.annotate_column('y', data_type='scalar')
        self.assertEqual(m.to_dict(), {"datacite": {"titles": [{'title': "Example dataset"}],
                                                    "creators": [], "publisher": "DLHub",
                                                    "resourceType": {"resourceTypeGeneral":
                                                                         "Dataset"},
                                                    "publicationYear": _year,
                                                    'identifier': {
                                                        'identifier': '10.YET/UNASSIGNED',
                                                        'identifierType': 'DOI'},
                                                    },
                                       "dlhub": {"version": __dlhub_version__,
                                                 "visible_to": ["public"],
                                                 "domain": ""},
                                       "dataset": {"location": data_path, "columns": [
                                           {"name": "x", "description": "Input variable",
                                            "type": "integer", "units": "cm"},
                                           {"name": "y", "type": "scalar"}],
                                                   "inputs": ["x"], "labels": ["y"],
                                                   "format": "csv", "read_options": {}}})
        validate_against_dlhub_schema(m.to_dict(), "dataset")


if __name__ == "__main__":
    unittest.main()
