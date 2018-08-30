"""Tests for models for generic Python functions"""

from dlhub_toolbox.models.servables.python import PickledClassServableModel
from sklearn import __version__ as skl_version
import unittest
import os


class TestPythonModels(unittest.TestCase):

    def test_pickle(self):
        pickle_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'model.pkl'))

        # Make the model
        model = PickledClassServableModel(pickle_path, 'predict_proba')

        # Make sure it throws value errors if inputs are not set
        with self.assertRaises(ValueError):
            model.to_dict()

        # Define the input and output types
        model.set_inputs('ndarray', 'Features for each entry', shape=(None, 4))
        model.set_outputs('ndarray', 'Predicted probabilities of being each iris species',
                          shape=(None, 3))

        # Add some requirements
        model.add_requirement('scikit-learn', 'detect')
        model.add_requirement('pytorch', 'latest')  # Deprecated project, version should stay same

        # Check the model output
        output = model.to_dict()
        self.assertEqual(output,
                         {'datacite':
                              {'creators': [], 'titles': [None], 'publisher': 'DLHub',
                               'resourceType': 'InteractiveResource'},
                          'dlhub': {'version': '0.1', 'domain': None, 'visible_to': ['public']},
                          'servable': {'langugage': 'python', 'type': 'pickled_class',
                                       'location': pickle_path,
                                       'run': {'handler': 'python_shim.run_class_method',
                                               'input': {'type': 'ndarray',
                                                         'description': 'Features for each entry',
                                                         'shape': (None, 4)},
                                               'output': {'type': 'ndarray',
                                                          'description': 'Predicted probabilities of being each iris species',
                                                          'shape': (None, 3)}},
                                       'method_details': {'class_name': 'SVC',
                                                          'method_name': 'predict_proba',
                                                          'default_args': {}},
                                       'requirements': {
                                           'scikit-learn': skl_version,
                                           'pytorch': '0.1.2'
                                       }}
                          })
        self.assertEqual([pickle_path], model.list_files())

