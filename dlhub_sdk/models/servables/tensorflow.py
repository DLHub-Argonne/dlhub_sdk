from typing import List

from dlhub_sdk.utils.types import compose_argument_block, simplify_numpy_dtype
from dlhub_sdk.models.servables import BaseServableModel
import tensorflow as tf
import numpy as np


def _convert_dtype(arg_type):
    """Get a DLHub type for a TensorFlow type

    Args:
        arg_type (int): Enumeration number of a Tensorflow Type
    Returns:
        (string) DLHub-schema-compatible name of the type
    """
    # Get the name of the type
    dtype = tf.DType(arg_type)
    return simplify_numpy_dtype(np.dtype(dtype.as_numpy_dtype))


def _read_tf_v1_inputs_and_outputs(arg_def):
    """Create a DLHub-compatible description from a Google ProtoBuf description of
    the inputs or outputs to a function

    Args:
        arg_def (MessageMap): Description of the inputs/outputs
    Returns:
        - (dict) Description of the input/output data in DLHub format
        - ([string]) Names of the input and output nodes
    """

    # Convert the tensor descriptions to a format compatible with DLHub,
    #   and fetch the names of the corresponding node on the graph
    dlhub_arg_defs = []
    node_names = []
    for name, arg_def in arg_def.items():
        # Get the shape of the Tensor (assuming all inputs are tensors)
        shape = [d.size if d.size != - 1 else None for d in arg_def.tensor_shape.dim]

        # Append the node name
        node_names.append(arg_def.name)

        # Make it an argument block
        dlhub_arg_defs.append(compose_argument_block('ndarray', name, shape,
                                                     _convert_dtype(arg_def.dtype)))

    # If the function has only one argument, return that
    if len(dlhub_arg_defs) == 1:
        return dlhub_arg_defs[0], node_names

    # Otherwise, create a "tuple" type
    #   First sort arguments by description, to ensure a deterministic order to them between runs
    dlhub_arg_defs, node_names = zip(*sorted(zip(dlhub_arg_defs, node_names),
                                             key=lambda x: x[0]['description']))
    return compose_argument_block('tuple', 'Arguments', shape=[len(dlhub_arg_defs)],
                                  element_types=dlhub_arg_defs), list(node_names)


def _read_tf_v2_function_signature(signature: List[tf.Tensor]) -> dict:
    """Generate a DLHub type specification from a Tensor object

    Args:
        sig: Function signature as a list of tensor
    Returns:
        (dict) Type specification
    """

    # Get the tensor shapes
    output = []
    for sig in signature:
        if sig.dtype != tf.resource:  # Sometimes gets added for single-input functions
            output.append(compose_argument_block('ndarray', sig.name, shape=list(sig.shape),
                                                 item_type=simplify_numpy_dtype(
                                                     np.dtype(sig.dtype.as_numpy_dtype))))
    if len(output) == 1:
        return output[0]
    else:
        return compose_argument_block('tuple', 'Several tensors', element_types=output)


class TensorFlowModel(BaseServableModel):
    """Class for generating descriptions of a TensorFlow model

    Assumes that a model has been saved using the :code:`tf.saved_model` module. Users
    must provide the output directory for the Tensorflow model, and this tool will infer
    all functions that were defined for this model.

    Note: DLHub assumes that the default method for a servable is "run" and TensorFlow assumes
    it to be :code:`tf.saved_model.signature_constants.DEFAULT_SERVING_SIGNATURE_DEF_KEY`
    (currently defined as "serving_default"). We will rename the default method to "run"
    """

    def _get_type(self):
        return 'TensorFlow Model'

    def _get_handler(self):
        return "tensorflow.TensorFlowServable"

    @classmethod
    def create_model(cls, export_directory):
        """Initialize the desription of a TensorFlow model

        Args:
            export_directory (string): Path to the output directory of a Tensorflow model
        """

        output = cls()
        if tf.__version__ < '2':
            return output._create_v1(export_directory)
        else:
            return output._create_v2(export_directory)

    def _create_v1(self, export_directory: str):
        """Internal method for `create_model` that is compatible with TF1"""

        # Load in the model
        with tf.Session() as sess:
            # Load in the model definition
            model_def = tf.saved_model.loader.load(sess, [tf.saved_model.tag_constants.SERVING],
                                                   export_directory)

        # Build descriptions for each function in the description
        for name, func_def in model_def.signature_def.items():
            # Get the descriptions for the inputs and outputs
            input_def, input_nodes = _read_tf_v1_inputs_and_outputs(func_def.inputs)
            output_def, output_nodes = _read_tf_v1_inputs_and_outputs(func_def.outputs)

            # Rename the default function
            if name == tf.saved_model.signature_constants.DEFAULT_SERVING_SIGNATURE_DEF_KEY:
                name = "run"

            # Register the function with the DLHub schema
            self.register_function(name, input_def, output_def,
                                   method_details={'input_nodes': input_nodes,
                                                   'output_nodes': output_nodes})

        # Check if there is a run method
        if 'run' not in self.servable.methods:
            raise ValueError('There is no default servable for this model.\n'
                             ' Make sure to use '
                             'tf.saved_model.signature_constants.DEFAULT_SERVING_SIGNATURE_DEF_KEY '
                             'when saving model.')

        # Add tensorflow version and files
        self.add_requirement('tensorflow', tf.__version__)
        self.add_directory(export_directory, recursive=True)

        return self

    def _create_v2(self, export_directory: str):
        """Internal method for `create_model` that is compatible with TF2"""

        # Load in the directory
        imported = tf.saved_model.load(export_directory)

        # Check that signatures are defined correctly
        if len(imported.signatures) == 0:
            raise ValueError('SavedModel does not contain any function signatures. '
                             'Please re-save model with function signatures. '
                             'See: https://www.tensorflow.org/guide/saved_model'
                             '#specifying_signatures_during_export')
        elif 'run' not in imported.signatures and \
                tf.saved_model.DEFAULT_SERVING_SIGNATURE_DEF_KEY not in imported.signatures:
            raise ValueError('SavedModel must contain a function '
                             'named "run" or the default signature key')

        # Build descriptions for each function in the description
        for name, func_def in imported.signatures.items():
            # Get the descriptions for the inputs and outputs
            input_spec = _read_tf_v2_function_signature(func_def.inputs)
            output_spec = _read_tf_v2_function_signature(func_def.outputs)

            # Rename the default function
            if name == tf.saved_model.DEFAULT_SERVING_SIGNATURE_DEF_KEY:
                name = "run"

            # Register the function with the DLHub schema
            self.register_function(name, input_spec, output_spec)

        # Add the files and tensorflow version
        self.add_requirement('tensorflow', imported.tensorflow_version)
        self.add_directory(export_directory, recursive=True)

        return self
