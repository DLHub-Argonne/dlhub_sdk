from datetime import datetime
import pickle as pkl
import os

from pytest import fixture, raises
from sklearn.svm import SVC
from sklearn import __version__ as skversion
import numpy as np

from dlhub_sdk.utils.schemas import validate_against_dlhub_schema
from dlhub_sdk.models.servables.sklearn import ScikitLearnModel


_year = str(datetime.now().year)
_svm_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'model.pkl'))


@fixture(autouse=True)
def setup():
    with open(_svm_path, 'wb') as fp:
        pkl.dump(SVC(probability=True), fp)


def test_load_model():
    model_path = _svm_path

    # Load the model
    model_info = ScikitLearnModel.create_model(model_path, n_input_columns=4, classes=3)
    model_info.set_title('Sklearn example').set_name('sklearn')

    # Print out the metadata
    metadata = model_info.to_dict()

    # Test key components
    assert metadata['dlhub']['dependencies']['python'] == {
        'scikit-learn': skversion
    }
    assert metadata['servable']['shim'] == 'sklearn.ScikitLearnServable'
    assert metadata['servable']['model_type'] == 'SVC'
    assert metadata['servable']['methods']['run'] == {
        "input": {
            "type": "ndarray",
            "shape": [None, 4],
            "description": ("List of records to evaluate with model. "
                            "Each record is a list of 4 variables."),
            "item_type": {
                "type": "float"
            }
        },
        "output": {
            "type": "ndarray",
            "shape": [None, 3],
            "description": "Probabilities for membership in each of 3 classes",
            "item_type": {
                "type": "float"
            }
        },
        "parameters": {},
        "method_details": {
            "method_name": "_predict_proba"
        }
    }
    assert metadata['servable']['model_summary'].startswith('SVC(')
    assert metadata['servable']['options'] == {
        'is_classifier': True,
        'serialization_method': 'pickle',
        'classes': ['Class 1', 'Class 2', 'Class 3']
    }

    # Check the schema validation
    validate_against_dlhub_schema(model_info.to_dict(), 'servable')


def test_regression():
    """Test a regression model saved with joblib"""
    model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'model-lr.pkl'))

    # Load the model
    if skversion > '0.23':
        with raises(ValueError):
            ScikitLearnModel.create_model(model_path, n_input_columns=2, serialization_method='joblib',
                                          classes=np.array(['number']))
    else:
        model_info = ScikitLearnModel.create_model(model_path, n_input_columns=2,
                                                   serialization_method='joblib',
                                                   classes=np.array(['number']))

        # Check that the metadata is as expected
        assert model_info.servable.methods["run"].method_details["method_name"] == "predict"
        assert model_info.list_files() == [model_path]
        assert model_info.servable.options["classes"] == ["number"]
        assert model_info.servable.methods["run"].output.shape == [None]
