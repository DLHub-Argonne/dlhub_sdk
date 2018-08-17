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
    """Metadata for a scikit-learn machine learning model"""

    def __init__(self, path, serialization_method="pickle"):
        """Initialize a scikit-learn model

        Args:
            path (string): Path to model file
            serialization_method (string): Library used to serialize model
        """
        # Set attributes
        self.path = path
        self.serialization_method = None
        super(ScikitLearnModel, self).__init__()

        # Create the metadata variables
        self.sklearn_version = None
        self.model_type = None

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
        self.model_type = type(model).__name__

    def to_dict(self):
        output = super(ScikitLearnModel, self).to_dict()

        # Store the model information
        output['servable'] = {
            'type': 'scikit-learn',
            'version': self.sklearn_version,
            'model_type': self.model_type
        }

        return output
