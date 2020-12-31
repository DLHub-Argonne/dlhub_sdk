"""Tests for models for generic Python functions"""
from jsonschema import ValidationError
from datetime import datetime
import pickle as pkl
import math
import os

from sklearn import __version__ as skl_version
from numpy import __version__ as numpy_version
from pytest import fixture, raises

from dlhub_sdk.models.servables.python import PythonClassMethodModel, \
    PythonStaticMethodModel
from dlhub_sdk.utils.schemas import validate_against_dlhub_schema
from dlhub_sdk.utils.types import compose_argument_block


_year = str(datetime.now().year)

_pickle_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'pickle.pkl'))


@fixture(autouse=True)
def setup():
    with open(_pickle_path, 'wb') as fp:
        pkl.dump(PythonClassMethodModel(), fp)


def test_pickle():
    # Make the model
    model = PythonClassMethodModel.create_model(_pickle_path, 'to_dict', {'fake': 'kwarg'})
    model.set_title('Python example').set_name("class_method")

    # Define the input and output types
    model.set_inputs('ndarray', 'Features for each entry', shape=[None, 4])
    model.set_outputs('ndarray', 'Predicted probabilities of being each iris species',
                      shape=[None, 3])

    # Make sure attempting to set "unpack" fails
    with raises(ValueError):
        model.set_unpack_inputs(True)

    # Add some requirements
    model.add_requirement('scikit-learn', 'detect')
    model.add_requirement('numpy', 'detect')
    model.add_requirement('sklearn', 'latest')  # Dummy project, version # shouldn't change

    # Check the model output
    output = model.to_dict()
    assert output['dlhub']['files'] == {'pickle': _pickle_path}
    assert output['dlhub']['dependencies']['python'] == {
        'scikit-learn': skl_version,
        'numpy': numpy_version,
        'sklearn': '0.0'
    }
    assert output['servable']['shim'] == 'python.PythonClassMethodServable'
    assert 'run' in output['servable']['methods']
    assert output['servable']['methods']['run']['input'] == {
        'type': 'ndarray',
        'description': 'Features for each entry',
        'shape': [None, 4]
    }
    assert output['servable']['methods']['run']['output'] == {
        'type': 'ndarray',
        'description': 'Predicted probabilities of being each iris species',
        'shape': [None, 3]
    }
    assert (output['servable']['methods']['run']
            ['method_details']['class_name'].endswith('.PythonClassMethodModel'))
    assert (output['servable']['methods']['run']
            ['method_details']['method_name'] == 'to_dict')

    assert [_pickle_path] == model.list_files()
    validate_against_dlhub_schema(output, 'servable')


def test_function():
    f = math.sqrt

    # Make the model
    model = PythonStaticMethodModel.from_function_pointer(f, autobatch=True)
    model.set_name("static_method").set_title('Python example')

    # Describe the inputs/outputs
    model.set_inputs('list', 'List of numbers', item_type='float')
    model.set_outputs('float', 'Square root of the number')

    # Generate the output
    output = model.to_dict()
    assert output['servable'] == {
            'type': 'Python static method',
            'shim': 'python.PythonStaticMethodServable',
            'options': {},
            'methods': {
                'run': {
                    'input': {
                        'type': 'list',
                        'description': 'List of numbers',
                        'item_type': {
                            'type': 'float'
                        }
                    },
                    'output': {
                        'type': 'float',
                        'description': 'Square root of the number'
                    },
                    'parameters': {},
                    'method_details': {
                        'module': 'math',
                        'method_name': 'sqrt',
                        'autobatch': True
                    }
                }
            }
        }
    validate_against_dlhub_schema(output, 'servable')


def test_multiarg():
    """Test making descriptions with more than one argument"""

    # Initialize the model
    model = PythonStaticMethodModel.from_function_pointer(max)
    model.set_name('test').set_title('test')

    # Define the inputs and outputs
    model.set_inputs('tuple', 'Two numbers',
                     element_types=[
                         compose_argument_block('float', 'A number'),
                         compose_argument_block('float', 'A second number')
                     ])
    model.set_outputs('float', 'Maximum of the two numbers')

    # Mark that the inputs should be unpacked
    model.set_unpack_inputs(True)

    # Check the description
    assert model.servable.methods['run'].dict(exclude_none=True) == {
        'input': {
            'type': 'tuple',
            'description': 'Two numbers',
            'element_types': [
                {'type': 'float', 'description': 'A number'},
                {'type': 'float', 'description': 'A second number'}
            ]
        },
        'output': {
            'type': 'float',
            'description': 'Maximum of the two numbers'
        },
        'method_details': {
            'module': 'builtins',
            'method_name': 'max',
            'unpack': True,
            'autobatch': False
        },
        'parameters': {}
    }

    validate_against_dlhub_schema(model.to_dict(), 'servable')


def test_visibility():
    model = PythonStaticMethodModel.create_model('numpy.linalg', 'norm')
    model.set_name('1d_norm')
    model.set_title('Norm of a 1D Array')
    model.set_inputs('ndarray', 'Array to be normed', shape=[None])
    model.set_outputs('number', 'Norm of the array')

    model.set_visibility(users=['bec215bc-9169-4be9-af49-4872b5e11ef8'])  # Setting visibility to a user
    validate_against_dlhub_schema(model.to_dict(), 'servable')
    assert model.dlhub.visible_to[0].startswith('urn:globus:auth:identity:')

    model.set_visibility(groups=['fdb38a24-03c1-11e3-86f7-12313809f035'])  # Setting visibility to a group
    validate_against_dlhub_schema(model.to_dict(), 'servable')
    assert len(model.dlhub.visible_to) == 1  # Ensure was replaced, not appended
    assert model.dlhub.visible_to[0].startswith('urn:globus:groups:id:')

    model.set_visibility(users=['foo'])  # Test using a non-UUID for user
    with raises(ValidationError):
        validate_against_dlhub_schema(model.to_dict(), 'servable')

    model.set_visibility()  # Default visibility is "public"
    validate_against_dlhub_schema(model.to_dict(), 'servable')
    assert model.dlhub.visible_to == ['public']
