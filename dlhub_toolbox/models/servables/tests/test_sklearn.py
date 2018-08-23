import unittest
import os

from dlhub_toolbox.models.servables.sklearn import ScikitLearnModel
from dlhub_toolbox.models import __dlhub_version__


class TestSklearn(unittest.TestCase):

    maxDiff = 2048

    def test_load_model(self):
        model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'model.pkl'))

        # Load the model
        model_info = ScikitLearnModel(model_path, n_input_columns=4, classes=3)
        expected = {'datacite': {'creators': [], 'publisher': 'DLHub',
                                 'titles': [None],
                                 'resourceType': "InteractiveResource"},
                    "dlhub": {"version": __dlhub_version__,
                              "visible_to": ["public"],
                              "domain": None},
                    'servable': {
                        'language': 'python',
                        'type': 'scikit-learn',
                        'location': model_path,
                        'version': '0.19.1',
                        'model_type': 'SVC',
                        'run': {
                            'handler': 'sklearn_shim.predict_on_batch',
                            "handler": "sklearn_shim.predict_on_batch",
                            "input": {
                                "type": "ndarray",
                                "shape": (None, 4),
                                "description": "List of records to evaluate with model. Each record is a list of 4 variables.",
                                "items": "float"
                            },
                            "output": {
                                "type": "ndarray",
                                "shape": (None, 3),
                                "description": "Predictions of the machine learning model.",
                                "items": "float"
                            }
                                 }}}
        self.assertEquals(model_info.to_dict(), expected)
