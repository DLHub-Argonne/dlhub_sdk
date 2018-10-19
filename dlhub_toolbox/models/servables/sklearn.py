from dlhub_toolbox.models.servables.python import BasePythonServableModel
from sklearn.base import is_classifier
from sklearn.pipeline import Pipeline
from sklearn.externals import joblib
import sklearn.base as sklbase
import pickle as pkl
import numpy as np
import inspect


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


class ScikitLearnModel(BasePythonServableModel):
    """Metadata for a scikit-learn machine learning model

    This class is build assuming that the inputs to the model will be a list
    of lists of fixed lengths. Models that take different kinds of inputs
    (e.g., Pipelines that include text-processing steps, KernelRidge models
    with custom kernel functions) will are not yet supported.
    """

    def __init__(self):
        super(ScikitLearnModel, self).__init__()

        # Create the metadata variables
        self.sklearn_version = None
        self.model_type = None
        self.classifier = None
        self.model_summary = None
        self.path = None
        self.serialization_method = "pickle"
        self.predict_options = {}

    @classmethod
    def create_model(cls, path, n_input_columns, classes=None, serialization_method="pickle"):
        """Initialize a scikit-learn model

        Args:
            path (string): Path to model file
            n_input_columns (int): Number of input columns for the model
            classes (Union[int,tuple]): For classification models, number of output classes or a
                list-like object with the names of the classes
            serialization_method (string): Library used to serialize model
        """
        # Load the model and get the method name, needed for instantiating the model type
        skl_version, model = ScikitLearnModel._load_model(path, serialization_method)
        method_name, method_kwargs = ScikitLearnModel._get_predict_method(model)
        output = super(ScikitLearnModel, cls).create_model(method_name, method_kwargs)

        # Set attributes
        output.serialization_method = serialization_method
        output.path = path
        output.sklearn_version = skl_version

        # Store the model input/output information
        output.n_input_columns = n_input_columns
        output.classes = classes
        if output.classes is not None:
            # Expand an integer if needed
            if isinstance(classes, int):
                output.classes = ['Class {}'.format(i+1) for i in range(classes)]
            elif isinstance(classes, np.ndarray):
                output.classes = list(output.classes)

        # Load other metadata
        output._inspect_model(model)

        # Define the path to the pickle
        output.add_file(path, 'model')

        # Add the sklearn requirement
        output.add_requirement("scikit-learn", output.sklearn_version)

        # Set default values for the run operation
        output.set_inputs("ndarray", 'List of records to evaluate with model. Each record is a list'
                                     ' of {} variables.'.format(output.n_input_columns),
                          item_type='float', shape=[None, output.n_input_columns])
        if "proba" in method_name:
            output.set_outputs("ndarray", 'Probabilities for membership '
                                          'in each of {} classes'.format(len(output.classes)),
                               shape=[None, len(output.classes)], item_type="float")
        else:
            output.set_outputs("ndarray", 'Predictions of the machine learning model.',
                               shape=[None],
                               item_type="float")

        return output

    @staticmethod
    def _load_model(path, serialization_method):
        """Load a scikit-learn model from disk to get basic metadata about

        Returns:
            - (string): Scikit-learn version
            - (BaseEstimator) A scikit-learn model object
        """

        # Load in the model
        global _sklearn_version_global
        _sklearn_version_global = None  # Set a default value
        if serialization_method == "pickle":
            with open(path, 'rb') as fp:
                model = pkl.load(fp)
        elif serialization_method == "joblib":
            model = joblib.load(path)
        else:
            raise Exception('Unknown serialization method: {}'.format(self.serialization_method))

        return _sklearn_version_global, model

    @staticmethod
    def _get_predict_method(model):
        """Get the name of the predict method for this model.

        The method name varies if the model is a classifier or not, and some scikit-learn models
        have arguments for the prediction function

        Args:
            model (BaseEstimator): Model to be inspected
        Returns:
            - (string) Name of the predict method
            - (dict) Any options for the predict method and their default values
        """
        # Store any special keyword arguments for the predict function
        model_obj = model.steps[-1][-1] if isinstance(model, Pipeline) else model
        predict_fun = model_obj.predict_proba if is_classifier(model) else model_obj.predict
        spec = inspect.signature(predict_fun)
        predict_options = dict((k, v.default) for k, v in spec.parameters.items() if k != "X")
        return predict_fun.__name__, predict_options

    def _inspect_model(self, model):
        """Extract metadata that describes an ML model

        Args:
            model (BaseEstimator): Model to be inspected
        Returns:
            function_name (string): Name of function to call for predict method
            predict_kwargs (dict): Dictionary of kwargs and default values for the predict function
        """
        self.pipeline = isinstance(model, Pipeline)
        self.model_type = type(model.steps[-1][-1]).__name__ \
            if self.pipeline else type(model).__name__

        # Get a summary about the model
        self.model_summary = str(model)  # sklearn prints out a text summary of the model

        # Determine whether the object is a classifier
        self.classifier = is_classifier(model)
        if self.classes is None and self.classifier:
            raise Exception('Classes (or at least number of classes) must be specified '
                            'in initializer for classifiers.')



    def to_dict(self, simplify_paths=False):
        output = super(ScikitLearnModel, self).to_dict(simplify_paths)

        # Store the model information
        output['servable'].update({
            'type': 'Scikit-learn estimator',
            'language': 'python',
            'model_type': self.model_type,
            'model_summary': self.model_summary,
            'options': {
                'serialization_method': self.serialization_method,
                'is_classifier': self.classifier,
                'classes': self.classes
            }
        })

        return output

    def _get_handler(self):
        return 'sklearn.ScikitLearnServable'

    def list_files(self):
        return [self.path]
