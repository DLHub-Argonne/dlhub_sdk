from datetime import datetime
import numpy as np
import unittest
import os

from dlhub_sdk.models.servables.sklearn import ScikitLearnModel
from dlhub_sdk import __dlhub_version__
from dlhub_sdk.utils.schemas import validate_against_dlhub_schema


_year = str(datetime.now().year)


class TestSklearn(unittest.TestCase):
    maxDiff = 4096

    def test_load_model(self):
        model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'model.pkl'))

        # Load the model
        model_info = ScikitLearnModel.create_model(model_path, n_input_columns=4, classes=3)
        model_info.set_title('Sklearn example').set_name('sklearn')
        expected = {'datacite': {'creators': [], 'publisher': 'DLHub',
                                 'titles': [{'title': 'Sklearn example'}],
                                 'resourceType': {'resourceTypeGeneral': "InteractiveResource"},
                                 'identifier': {'identifier': '10.YET/UNASSIGNED',
                                                'identifierType': 'DOI'},
                                 'publicationYear': _year,
                                 "descriptions": [],
                                 "fundingReferences": [],
                                 "relatedIdentifiers": [],
                                 "alternateIdentifiers": [],
                                 "rightsList": []},
                    "dlhub": {"version": __dlhub_version__,
                              "visible_to": ["public"], 'name': 'sklearn',
                              "domains": [], "id": None,
                              'files': {'model': model_path}},
                    'servable': {
                        'language': 'python',
                        'type': 'Scikit-learn estimator',
                        'dependencies': {
                            'python': {'scikit-learn': '0.19.1'}
                        },
                        'model_type': 'SVC',
                        'shim': 'sklearn.ScikitLearnServable',
                        'methods': {
                            'run': {"input": {
                                    "type": "ndarray",
                                    "shape": [None, 4],
                                    "description": "List of records to evaluate with model. Each record is a list of 4 variables.",
                                    "item_type": {"type": "float"}
                                }, "output": {
                                    "type": "ndarray",
                                    "shape": [None, 3],
                                    "description": "Probabilities for membership in each of 3 classes",
                                    "item_type": {"type": "float"}
                                },
                                "parameters": {},
                                "method_details": {
                                    "method_name": "_predict_proba"
                                }
                            }
                        },
                        'model_summary': "SVC(C=1, cache_size=200, class_weight=None, coef0=0.0,\n"
                                         "  decision_function_shape='ovr', degree=3, gamma='auto', kernel='linear',\n"
                                         "  max_iter=-1, probability=True, random_state=None, shrinking=True,\n"
                                         "  tol=0.001, verbose=False)",
                        'options': {
                            'is_classifier': True,
                            'serialization_method': 'pickle',
                            'classes': ['Class 1', 'Class 2', 'Class 3']
                        }
                    }}
        self.assertEquals(model_info.to_dict(), expected)
        validate_against_dlhub_schema(model_info.to_dict(), 'servable')

    def test_regression(self):
        """Test a regression model saved with joblib"""
        model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'model-lr.pkl'))

        # Load the model
        model_info = ScikitLearnModel.create_model(model_path, n_input_columns=2,
                                                   serialization_method='joblib',
                                                   classes=np.array(['number']))

        # Check that the metadata is as expected
        self.assertEqual(model_info["servable"]["methods"]["run"]["method_details"]["method_name"],
                         "predict")
        self.assertEqual([model_path], model_info.list_files())
        self.assertEqual(['number'], model_info["servable"]["options"]["classes"])
        self.assertEqual([None], model_info["servable"]["methods"]["run"]['output']['shape'])
