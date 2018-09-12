from dlhub_toolbox.models.servables.python import BasePythonServableModel
from sklearn.base import is_classifier
from sklearn.pipeline import Pipeline
from sklearn.externals import joblib
import sklearn.base as sklbase
import pickle as pkl
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

    def __init__(self, path, n_input_columns, classes=None, serialization_method="pickle"):
        """Initialize a scikit-learn model

        Args:
            path (string): Path to model file
            n_input_columns (int): Number of input columns for the model
            classes (Union[int,tuple]): For classification models, number of output classes or a
                list-like object with the names of the classes
            serialization_method (string): Library used to serialize model
        """
        # Set attributes
        self.path = path
        self.serialization_method = serialization_method

        # Create the metadata variables
        self.sklearn_version = None
        self.model_type = None
        self.classifier = None
        self.model_summary = None
        self.predict_options = {}

        # Store the model input/output information
        self.n_input_columns = n_input_columns
        self.classes = classes
        if self.classes is not None:
            # Expand an integer if needed
            if isinstance(classes, int):
                self.classes = ['Class {}'.format(i+1) for i in range(classes)]

        # Load other metadata
        model = self._load_model()
        method_name, method_kwargs = self._inspect_model(model)
        super(ScikitLearnModel, self).__init__(method_name, method_kwargs)

        # Add the sklearn requirement
        self.add_requirement("scikit-learn", self.sklearn_version)

        # Set default values for the run operation
        self.set_inputs("ndarray", 'List of records to evaluate with model. '
                                   'Each record is a list '
                                   'of {} variables.'.format(self.n_input_columns),
                        item_type='float', shape=[None, self.n_input_columns])
        if "proba" in method_name:
            self.set_outputs("ndarray", 'Probabilities for membership '
                                        'in each of {} classes'.format(len(self.classes)),
                             shape=[None, len(self.classes)], item_type="float")
        else:
            self.set_outputs("ndarray", 'Predictions of the machine learning model.', shape=[None],
                             item_type="float")

    def _load_model(self):
        """Load a scikit-learn model from disk and extract basic metadata

        Returns:
            (BaseEstimator) A scikit-learn model object
        """

        # Load in the model
        global _sklearn_version_global
        _sklearn_version_global = None  # Set a default value
        if self.serialization_method == "pickle":
            with open(self.path, 'rb') as fp:
                model = pkl.load(fp)
        elif self.serialization_method == "joblib":
            model = joblib.load(self.path)
        else:
            raise Exception('Unknown serialization method: {}'.format(self.serialization_method))

        # Get some basic information about the model
        self.sklearn_version = _sklearn_version_global  # Stolen during the unpickling process

        return model

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

        # Store any special keyword arguments for the predict function
        model_obj = model.steps[-1][-1] if self.pipeline else model
        predict_fun = model_obj.predict_proba if self.classifier else model_obj.predict
        spec = inspect.signature(predict_fun)
        predict_options = dict((k, v.default) for k, v in spec.parameters.items() if k != "X")
        return predict_fun.__name__, predict_options

    def to_dict(self):
        output = super(ScikitLearnModel, self).to_dict()

        # Store the model information
        output['servable'].update({
            'type': 'Scikit-learn estimator',
            'files': {'model': self.path},
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

    def _get_method_details(self):
        return {}

    def list_files(self):
        return [self.path]
