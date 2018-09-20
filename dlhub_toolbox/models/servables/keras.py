from keras import __version__ as keras_version
from keras.models import load_model

from dlhub_toolbox.models.servables.python import BasePythonServableModel
from dlhub_toolbox.utils.types import compose_argument_block


_keras_version_tuple = tuple(int(i) for i in keras_version.split("."))


class KerasModel(BasePythonServableModel):
    """Servable based on a Keras Model object.

    Assumes that the model has been saved to an hdf5 file"""

    def __init__(self, model_path, output_names):
        """Initialize a Keras model.

        Args:
            model_path (string): Path to the hd5 file that describes a model and the weights
            output_names ([string] or [[string]]): Names of output classes. If applicable, one list for
                each output layer
        """

        super(KerasModel, self).__init__('predict')

        # Save model information
        self.model_path = model_path
        self.output_names = output_names

        # Add model as a file to be sent
        self.add_file(self.model_path, 'model')

        # Get the model details
        model = load_model(self.model_path)

        # Get the inputs of the model
        self.input = self._format_layer_spec(model.input_shape)
        self.output = self._format_layer_spec(model.output_shape)

        # Get a full description of the model
        self.summary = ""

        def capture_summary(x):
            self.summary += x + "\n"
        model.summary(print_fn=capture_summary)

        # Add keras as a dependency
        self.add_requirement('keras', keras_version)
        self.add_requirement('h5py', 'detect')

    def _format_layer_spec(self, layers):
        """Make a description of a list of input or output layers

        Args:
            layers (tuple or [tuple]): Shape of the layers
        Return:
            (dict) Description of the inputs / outputs
        """
        if isinstance(layers, tuple):
            return compose_argument_block("ndarray", "Tensor", shape=layers)
        else:
            return compose_argument_block("list", "List of tensors",
                                          item_type=[self._format_layer_spec(i) for i in layers])

    def _get_method_details(self):
        output = super(KerasModel, self)._get_method_details()
        output['classes'] = self.output_names
        return output

    def _get_handler(self):
        return "keras.KerasServable"

    def to_dict(self, simplify_paths=False):
        output = super(KerasModel, self).to_dict(simplify_paths)

        # Add in some general metadata
        output['servable']['type'] = 'Keras Model'
        output['servable']['model_type'] = 'Deep NN'
        output['servable']['model_summary'] = self.summary

        return output
