from sklearn.base import is_classifier
from sklearn.pipeline import Pipeline

from dlhub_toolbox.models.servables import BaseServableModel
import pickle as pkl
from sklearn.externals import joblib

import sklearn.base as sklbase


# scikit-learn stores the version used to create a model in the pickle file,
#  but deletes it before unpickling the object. This code intercepts the version
#  number before it gets deleted

_sklearn_version_global = None
_original_set_state = sklbase.BaseEstimator.__setstate__


def _hijack_baseestimator_setstate(self, state):
    global _sklearn_version_global
    _sklearn_version_global = state.get("_sklearn_version", "pre-0.18")
    _original_set_state(self, state)

sklbase.BaseEstimator.__setstate__ = _hijack_baseestimator_setstate


class ScikitLearnModel(BaseServableModel):
    """Metadata for a scikit-learn machine learning model

    This class is build assuming that the inputs to the model will be a list
    of lists of fixed lengths. Models that take different kinds of inputs
    (e.g., Pipelines that include text-processing steps, KernelRidge models
    with custom kernel functions) will are not yet supported.
    """

    def __init__(self, path, n_input_columns, classes=None, serialization_method="pickle"):
        """Initialize a scikit-learn model

        Args:
            path (string): Path to model file
            n_input_columns (int): Number of input columns for the model
            classes (Union[int,tuple]): For classication models, number of output classes or a
                list-like object with the namess of the classes
            serialization_method (string): Library used to serialize model
        """
        # Set attributes
        self.path = path
        self.serialization_method = None
        super(ScikitLearnModel, self).__init__()

        # Create the metadata variables
        self.sklearn_version = None
        self.model_type = None
        self.classifier = None
        self.model_summary = None

        # Store the model input/output information
        self.n_input_columns = n_input_columns
        self.classes = classes
        if self.classes is not None:
            # Expand an integer if needed
            if isinstance(classes, int):
                self.classes = ['Class {}'.format(i+1) for i in range(classes)]

        # Load other metadata
        self.load_model(path, serialization_method)

    def load_model(self, path, serialization_method="pickle"):
        """Load a scikit-learn model from disk and extract metadata

        Args:
            path (string): Path to model file
            serialization_method (string): Library used to serialize model
        """

        # Save the model and serialization method
        self.path = path
        self.serialization_method = serialization_method

        # Load in the model
        global _sklearn_version_global
        _sklearn_version_global = None  # Set a default value
        if serialization_method == "pickle":
            with open(path, 'rb') as fp:
                model = pkl.load(fp)
        elif serialization_method == "joblib":
            model = joblib.load(path)
        else:
            raise Exception('Unknown serialization method: {}'.format(serialization_method))

        # Get some basic information about the model
        self.sklearn_version = _sklearn_version_global  # Stolen during the unpickling process
        self.model_type = type(model.steps[-1][-1]).__name__ \
                if isinstance(model, Pipeline) else type(model).__name__

        # Get a summary about the model
        self.model_summary = str(model)  # sklearn prints out a text summary of the model

        # Determine whether the object is a classifier
        self.classifier = is_classifier(model)
        if self.classes is None and self.classifier:
            raise Exception('Classes (or at least number of classes) must be specified '
                            'in initializer for classifiers.')

    def to_dict(self):
        output = super(ScikitLearnModel, self).to_dict()

        # Store the model information
        output['servable'].update({
            'type': 'scikit-learn',
            'version': self.sklearn_version,
            'location': self.path,
            'language': 'python',
            'model_type': self.model_type,
            'model_summary': self.model_summary
        })

        return output

    def _get_handler(self):
        return 'sklearn_shim.predict_on_batch'

    def _get_input(self):
        return {
            'type': 'ndarray',
            'shape': (None, self.n_input_columns),
            'description': 'List of records to evaluate with model. Each record is '
                           'a list of {} variables.'.format(self.n_input_columns),
            'items': 'float'
        }

    def _get_output(self):
        return {
            'type': 'ndarray',
            'shape': (None, 1 if self.classes is None else len(self.classes)),
            'description': 'Predictions of the machine learning model.' if not self.classifier else
                    'Probabilities for membership in each of {} classes'.format(len(self.classes)),
            'items': 'float'
        }

    def list_files(self):
        return [self.path]
