import torch

from dlhub_sdk.models.servables import ArgumentTypeMetadata
from dlhub_sdk.models.servables.python import BasePythonServableModel
from dlhub_sdk.utils.types import compose_argument_block


class TorchModel(BasePythonServableModel):
    """Servable based on a Torch Model object.

    Assumes that the model has been saved to a pt or a pth file"""

    @classmethod
    def create_model(cls, model_path, input_shape, output_shape,
                     input_type='float', output_type='float'):
        """Initialize a PyTorch model.

        Args:
            model_path (string): Path to the pt or pth file that contains the weights and
                the architecture
            input_shape (tuple or [tuple]): Shape of input matrix to model
            output_shape (tuple or [tuple]): Shape of output matrix from model
            input_type (str or [str]): Data type of inputs
            output_type (str or [str]): Data type of outputs
       """
        output: TorchModel = super().create_model('__call__')

        # Add model as a file to be sent
        output.add_file(model_path, 'model')

        # Get the model details
        if model_path.endswith('.pt') or model_path.endswith('.pth'):
            model = torch.load(model_path)
        else:
            raise ValueError('File type for architecture not recognized')

        # Get the inputs of the model
        output.servable.methods['run'].input = output.format_layer_spec(input_shape, input_type)
        output.servable.methods['run'].output = output.format_layer_spec(output_shape, output_type)

        output.servable.model_summary = str(model)
        output.servable.model_type = 'Deep NN'

        # Add torch as a dependency
        output.add_requirement('torch', torch.__version__)

        return output

    def format_layer_spec(self, layers, datatypes):
        """Make a description of a list of input or output layers

        Args:
            layers (tuple or [tuple]): Shape of the layers
            datatypes (str or [str]): Data type of each input layer
        Return:
            (dict) Description of the inputs / outputs
        """
        if isinstance(layers, tuple):
            return ArgumentTypeMetadata.parse_obj(compose_argument_block("ndarray", "Tensor",
                                                                         shape=list(layers), item_type=datatypes))
        else:
            if isinstance(datatypes, str):
                datatypes = [datatypes] * len(layers)
            return ArgumentTypeMetadata.parse_obj(
                compose_argument_block("tuple", "Tuple of tensors",
                                       element_types=[self.format_layer_spec(i, t)
                                                      for i, t in zip(layers, datatypes)]))

    def _get_handler(self):
        return "torch.TorchServable"

    def _get_type(self):
        return "Torch Model"
