from datetime import datetime
import unittest
import os

from dlhub_toolbox.models.servables.sklearn import ScikitLearnModel
from dlhub_toolbox.models import __dlhub_version__
from dlhub_toolbox.utils.schemas import validate_against_dlhub_schema


_year = str(datetime.now().year)


class TestSklearn(unittest.TestCase):
    maxDiff = 4096

    def test_load_model(self):
        model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'model.pkl'))

        # Load the model
        model_info = ScikitLearnModel(model_path, n_input_columns=4, classes=3)
        model_info.set_title('Sklearn example')
        expected = {'datacite': {'creators': [], 'publisher': 'DLHub',
                                 'titles': [{'title': 'Sklearn example'}],
                                 'resourceType': {'resourceTypeGeneral': "InteractiveResource"},
                                 'identifier': {'identifier': '10.YET/UNASSIGNED',
                                                'identifierType': 'DOI'},
                                 'publicationYear': _year,
                                 },
                    "dlhub": {"version": __dlhub_version__,
                              "visible_to": ["public"],
                              "domain": "", "id": None},
                    'servable': {
                        'language': 'python',
                        'type': 'scikit-learn',
                        'location': model_path,
                        'dependencies': {
                            'python': {'scikit-learn': '0.19.1'}
                        },
                        'model_type': 'SVC',
                        'run': {
                            'handler': 'sklearn_shim.predict_on_batch',
                            "input": {
                                "type": "ndarray",
                                "shape": [None, 4],
                                "description": "List of records to evaluate with model. Each record is a list of 4 variables.",
                                "items": "float"
                            },
                            "output": {
                                "type": "ndarray",
                                "shape": [None, 3],
                                "description": "Probabilities for membership in each of 3 classes",
                                "items": "float"
                            },
                            "parameters": {}
                        },
                        'model_summary': "SVC(C=1, cache_size=200, class_weight=None, coef0=0.0,\n"
                                         "  decision_function_shape='ovr', degree=3, gamma='auto', kernel='linear',\n"
                                         "  max_iter=-1, probability=True, random_state=None, shrinking=True,\n"
                                         "  tol=0.001, verbose=False)"
                    }}
        self.assertEquals(model_info.to_dict(), expected)
        validate_against_dlhub_schema(model_info.to_dict(), 'servable')
