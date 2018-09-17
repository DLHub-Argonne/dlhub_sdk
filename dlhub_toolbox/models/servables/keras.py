from keras import __version__ as keras_version
from keras.models import load_model

from dlhub_toolbox.models.servables.python import BasePythonServableModel
from dlhub_toolbox.utils.types import compose_argument_block


class KerasModel(BasePythonServableModel):
    """Servable based on a Keras Model object.

    Assumes that the model has been saved to an hdf5 file"""

    def __init__(self, model_path):
        """Initialize a Keras model.

        Args:
            model_path (string): Path to the hd5 file that describes a model and the weights
        """

        super(KerasModel, self).__init__('predict')

        # Load in the model information
        self.model_path = model_path

        # Add model as a file to be sent
        self.add_file(self.model_path, 'model')

        # Get the model details
        model = load_model(self.model_path)

        # Get the inputs of the model
        self.input = self.get_layer_shape(model.input_layers, True)
        self.output = self.get_layer_shape(model.output_layers, False)

        # Get a full description of the model
        self.summary = ""

        def capture_summary(x):
            self.summary += x + "\n"
        model.summary(print_fn=capture_summary)

        # Add keras as a depedency
        self.add_requirement('keras', keras_version)
        self.add_requirement('h5py', 'detect')

    def get_layer_shape(self, layers, get_input=True):
        """Get a description of a list of input or output layers

        Args:
            layers ([Layer]): Input or output layer(s) of a Keras model
            get_input (bool): Whether to get input or output layers
        Return:
            (dict) Description of the inputs / outputs
        """
        if len(layers) == 1:
            return compose_argument_block("ndarray", "Tensor",
                                          layers[0].input_shape if get_input else
                                          layers[0].output_shape)
        else:
            return compose_argument_block("list", "List of tensors",
                                          item_type=[self.get_layer_shape([i], get_input)
                                                     for i in layers])

    def _get_handler(self):
        return "keras.KerasServable"

    def to_dict(self):
        output = super(KerasModel, self).to_dict()

        # Add in some general metadata
        output['servable']['type'] = 'Keras Model'
        output['servable']['model_type'] = 'Deep NN'
        output['servable']['model_summary'] = self.summary

        return output
