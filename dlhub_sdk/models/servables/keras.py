from keras import __version__ as keras_version
from keras.models import load_model

from dlhub_sdk.models.servables.python import BasePythonServableModel
from dlhub_sdk.utils.types import compose_argument_block


_keras_version_tuple = tuple(int(i) for i in keras_version.split("."))


class KerasModel(BasePythonServableModel):
    """Servable based on a Keras Model object.

    Assumes that the model has been saved to an hdf5 file"""

    @classmethod
    def create_model(cls, model_path, output_names):
        """Initialize a Keras model.

           Args:
               model_path (string): Path to the hd5 file that describes a model and the weights
               output_names ([string] or [[string]]): Names of output classes. If applicable, one list for
                   each output layer
       """
        output = super(KerasModel, cls).create_model('predict')

        # Add model as a file to be sent
        output.add_file(model_path, 'model')

        # Get the model details
        model = load_model(model_path)

        # Get the inputs of the model
        output['servable']['methods']['run']['input'] = output.format_layer_spec(model.input_shape)
        output['servable']['methods']['run']['output'] = output.format_layer_spec(model.output_shape)
        output['servable']['methods']['run']['method_details']['classes'] = output_names

        # Get a full description of the model
        output.summary = ""

        def capture_summary(x):
            output.summary += x + "\n"
        model.summary(print_fn=capture_summary)
        output['servable']['model_summary'] = output.summary
        output['servable']['model_type'] = 'Deep NN'

        # Add keras as a dependency
        output.add_requirement('keras', keras_version)
        output.add_requirement('h5py', 'detect')
        return output

    def format_layer_spec(self, layers):
        """Make a description of a list of input or output layers

        Args:
            layers (tuple or [tuple]): Shape of the layers
        Return:
            (dict) Description of the inputs / outputs
        """
        if isinstance(layers, tuple):
            return compose_argument_block("ndarray", "Tensor", shape=list(layers))
        else:
            return compose_argument_block("tuple", "Tuple of tensors",
                                          element_types=[self.format_layer_spec(i) for i in layers])

    def _get_handler(self):
        return "keras.KerasServable"

    def _get_type(self):
        return "Keras Model"
