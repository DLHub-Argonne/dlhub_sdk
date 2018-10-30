"""Tests for models for generic Python functions"""

from dlhub_sdk.models.servables.python import PythonClassMethodModel, \
    PythonStaticMethodModel
from dlhub_sdk import __dlhub_version__
from sklearn import __version__ as skl_version
from numpy import __version__ as numpy_version
from datetime import datetime
import unittest
import math
import os

from dlhub_sdk.utils.schemas import validate_against_dlhub_schema


_year = str(datetime.now().year)


class TestPythonModels(unittest.TestCase):

    maxDiff = 4096

    def test_pickle(self):
        pickle_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'model.pkl'))

        # Make the model
        model = PythonClassMethodModel.create_model(pickle_path, 'predict_proba', {'fake': 'kwarg'})
        model.set_title('Python example').set_name("class_method")

        # Make sure it throws value errors if inputs are not set
        with self.assertRaises(ValueError):
            model.to_dict()

        # Define the input and output types
        model.set_inputs('ndarray', 'Features for each entry', shape=[None, 4])
        model.set_outputs('ndarray', 'Predicted probabilities of being each iris species',
                          shape=[None, 3])

        # Add some requirements
        model.add_requirement('scikit-learn', 'detect')
        model.add_requirement('numpy', 'detect')
        model.add_requirement('theano', 'latest')  # Deprecated project, version should stay same

        # Check the model output
        output = model.to_dict()
        self.assertEqual(output,
                         {'datacite':
                              {'creators': [], 'titles': [{'title': 'Python example'}],
                               'publisher': 'DLHub',
                               'resourceType': {'resourceTypeGeneral': 'InteractiveResource'},
                               'identifier': {'identifier': '10.YET/UNASSIGNED',
                                              'identifierType': 'DOI'},
                               'publicationYear': _year,
                               "descriptions": [],
                               "fundingReferences": [],
                               "relatedIdentifiers": [],
                               "alternateIdentifiers": [],
                               "rightsList": []
                               },
                          'dlhub': {'version': '0.1', 'domains': [], 'visible_to': ['public'],
                                    "id": None, "name": "class_method",
                                    'files': {'pickle': pickle_path}},
                          'servable': {'language': 'python', 'type': 'Python class method',
                                       'shim': 'python.PythonClassMethodServable',
                                       'methods': {'run': {'input': {'type': 'ndarray',
                                                                     'description': 'Features for each entry',
                                                                     'shape': [None, 4]},
                                                           'output': {'type': 'ndarray',
                                                                      'description': 'Predicted probabilities of being each iris species',
                                                                      'shape': [None, 3]},
                                                           'parameters': {'fake': 'kwarg'},
                                                           'method_details': {
                                                               'class_name': 'sklearn.svm.classes.SVC',
                                                               'method_name': 'predict_proba'},
                                                           }},
                                       'dependencies': {
                                           'python': {
                                               'scikit-learn': skl_version,
                                               'numpy': numpy_version,
                                               'theano': '1.0.3'
                                           }}
                          }})
        self.assertEqual([pickle_path], model.list_files())
        validate_against_dlhub_schema(output, 'servable')

    def test_function(self):
        f = math.sqrt

        # Make the model
        model = PythonStaticMethodModel.from_function_pointer(f, autobatch=True)
        model.set_name("static_method").set_title('Python example')

        # Describe the inputs/outputs
        model.set_inputs('list', 'List of numbers', item_type='float')
        model.set_outputs('float', 'Square root of the number')

        # Generate the output
        output = model.to_dict()
        self.assertEqual(output,
                         {'datacite':
                              {'creators': [], 'titles': [{'title': 'Python example'}],
                               'publisher': 'DLHub',
                               'resourceType': {'resourceTypeGeneral': 'InteractiveResource'},
                               'identifier': {'identifier': '10.YET/UNASSIGNED',
                                              'identifierType': 'DOI'},
                               'publicationYear': _year,
                               "descriptions": [],
                               "fundingReferences": [],
                               "relatedIdentifiers": [],
                               "alternateIdentifiers": [],
                               "rightsList": []
                           },
                          'dlhub': {'version': __dlhub_version__, 'domains': [], 'visible_to': ['public'],
                                    "id": None, "name": "static_method",
                                    'files': {}},
                          'servable': {'language': 'python', 'type': 'Python static method',
                                       'shim': 'python.PythonStaticMethodServable',
                                       'methods': {'run': {'input': {'type': 'list',
                                                                     'description': 'List of numbers',
                                                                     'item_type': {
                                                                         'type': 'float'}},
                                                           'output': {'type': 'float',
                                                                      'description': 'Square root of the number'},
                                                           'parameters': {},
                                                           'method_details': {'module': 'math',
                                                                              'method_name': 'sqrt',
                                                                              'autobatch': True}}
                                                   },
                                       'dependencies': {'python': {}}}
                          })
        validate_against_dlhub_schema(output, 'servable')
