from dlhub_sdk.models.servables.python import BasePythonServableModel
from sklearn.base import is_classifier
from sklearn.pipeline import Pipeline
import sklearn.base as sklbase
import pickle as pkl
import inspect

# Get a version of joblib
try:
    from sklearn.externals import joblib
except ImportError:
    try:
        import joblib
    except ImportError:
        joblib = None

# scikit-learn stores the version used to create a model in the pickle file,
#  but deletes it before unpickling the object. This code intercepts the version
#  number before it gets deleted

_sklearn_version_global = None
_original_set_state = sklbase.BaseEstimator.__setstate__


def _hijack_baseestimator_setstate(self, state):
    global _sklearn_version_global
    _sklearn_version_global = state.get("_sklearn_version", "pre-0.18")
    _original_set_state(self, state)


# Define the override
sklbase.BaseEstimator.__setstate__ = _hijack_baseestimator_setstate


class ScikitLearnModel(BasePythonServableModel):
    """Metadata for a scikit-learn machine learning model

    This class is build assuming that the inputs to the model will be a list
    of lists of fixed lengths. Models that take different kinds of inputs
    (e.g., Pipelines that include text-processing steps, KernelRidge models
    with custom kernel functions) will are not yet supported.
    """

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
        output: ScikitLearnModel = super(ScikitLearnModel, cls).create_model(method_name, method_kwargs)

        # Save the serialization method
        output.servable.options = {"serialization_method": serialization_method}

        # Save the classes, if present
        if classes is not None:
            if isinstance(classes, int):
                classes = ['Class {}'.format(i+1) for i in range(classes)]
            output.servable.options["classes"] = list(classes)

        # Store the model input/output information
        n_input_columns = n_input_columns
        classes = classes

        # Load other metadata
        output.inspect_model(model)

        # Define the path to the pickle
        output.add_file(path, 'model')

        # Add the sklearn requirement
        output.add_requirement("scikit-learn", skl_version)

        # Set default values for the run operation
        output.set_inputs("ndarray", 'List of records to evaluate with model. Each record is a list'
                                     ' of {} variables.'.format(n_input_columns),
                          item_type='float', shape=[None, n_input_columns])
        if "proba" in method_name:
            output.set_outputs("ndarray", 'Probabilities for membership '
                                          'in each of {} classes'.format(len(classes)),
                               shape=[None, len(classes)], item_type="float")
        else:
            output.set_outputs("ndarray", 'Predictions of the machine learning model.',
                               shape=[None],
                               item_type="float")

        return output

    def _get_type(self):
        return 'Scikit-learn estimator'

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
            if joblib is None:
                raise ImportError('joblib was not installed')
            try:
                model = joblib.load(path)
            except ModuleNotFoundError:
                raise ValueError('Model saved with sklearn.external.joblib. '
                                 'Please install sklearn version 0.19.2 or earlier')
        else:
            raise Exception('Unknown serialization method: {}'.format(serialization_method))

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

        # Determine which function we call to make a prediction based on whether we are a classifier or regressor
        model_obj = model.steps[-1][-1] if isinstance(model, Pipeline) else model
        predict_fun = model_obj.predict_proba if is_classifier(model) else model_obj.predict

        # Find any additional arguments for the method (e.g., return_std for GPR models)
        spec = inspect.signature(predict_fun)
        predict_options = dict((k, v.default) for k, v in spec.parameters.items()
                               if k not in ["X", "self"])  # Skip if parameter is "self" or "X" (we know about them)
        return predict_fun.__name__, predict_options

    def inspect_model(self, model):
        """Extract and store metadata that describes an ML model

        Args:
            model (BaseEstimator): Model to be inspected
        """
        pipeline = isinstance(model, Pipeline)

        # Save the model type
        self.servable.model_type = type(model.steps[-1][-1]).__name__ if pipeline else type(model).__name__

        # Get a summary about the model
        # sklearn prints out a text summary of the model
        self.servable.model_summary = str(model)

        # Determine whether the object is a classifier
        is_clfr = is_classifier(model)
        self.servable.options["is_classifier"] = is_clfr
        if "classes" not in self.servable.options and is_clfr:
            raise Exception('Classes (or at least number of classes) must be specified '
                            'in initializer for classifiers.')

    def _get_handler(self):
        return 'sklearn.ScikitLearnServable'
