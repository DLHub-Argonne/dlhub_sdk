import logging

try:
    import keras as keras_keras
except ImportError:
    keras_keras = None
try:
    from tensorflow import keras as tf_keras
except ImportError:
    tf_keras = None

from dlhub_sdk.models.servables.python import BasePythonServableModel
from dlhub_sdk.models.servables import ArgumentTypeMetadata
from dlhub_sdk.utils.types import compose_argument_block

logger = logging.getLogger(__name__)
_summary_limit = 10000


def _detect_backend(keras, output):
    """Add the backend

    Args:
        output (KerasModel): Current description of Keras model, will be modified
    """

    # Determine the name of the object
    my_backend = keras.backend.backend().lower()

    # Add it as a requirement
    output.add_requirement(my_backend, 'detect')


class KerasModel(BasePythonServableModel):
    """Servable based on a Keras Model object.

    Assumes that the model has been saved to an hdf5 file"""

    @classmethod
    def create_model(cls, model_path, output_names=None, arch_path=None,
                     custom_objects=None, force_tf_keras: bool = False) -> 'KerasModel':
        """Initialize a Keras model.

        Args:
            model_path (string): Path to the hd5 file that contains the weights and, optionally,
                the architecture
            output_names ([string] or [[string]]): Names of output classes.
            arch_path (string): Path to the hd5 model containing the architecture, if not
                available in the file at :code:`model_path`.
            custom_objects (dict): Map of layer names to custom layers. See
                `Keras Documentation
                <https://www.tensorflow.org/api_docs/python/tf/keras/models/load_model>`_
                for more details.
            force_tf_keras (bool): Force the use of TF.Keras even if keras is installed
       """
        output: KerasModel = super().create_model('predict')
        if force_tf_keras:
            if tf_keras is None:
                raise ValueError('You forced tf_keras but do not have tensorflow.keras')
            keras = tf_keras
            use_tf_keras = True
        elif keras_keras is not None:
            # Use old keras by default, as users may have gone out of their way to install it
            keras = keras_keras
            use_tf_keras = False
            if tf_keras is not None:
                logging.warning('Model publication will use standalone keras, yet you have tf.keras installed. '
                                'If you want your model to use tf.keras, use ``force_tf_keras=True``.')
        elif tf_keras is not None:
            keras = tf_keras
            use_tf_keras = True
        else:
            raise ValueError('You do not have any version of keras installed.')

        # Add model as a file to be sent
        output.add_file(model_path, 'model')
        if arch_path is not None:
            output.add_file(arch_path, 'arch')

        # Store the list of custom objects
        if custom_objects is not None:
            for k, v in custom_objects.items():
                output.add_custom_object(k, v)

        # Get the model details
        if arch_path is None:
            model = keras.models.load_model(model_path, custom_objects=custom_objects)
        else:
            if arch_path.endswith('.h5') or arch_path.endswith('.hdf') \
                    or arch_path.endswith('.hdf5') or arch_path.endswith('.hd5'):
                model = keras.models.load_model(arch_path,
                                                custom_objects=custom_objects, compile=False)
            elif arch_path.endswith('.json'):
                with open(arch_path) as fp:
                    json_string = fp.read()
                model = keras.models.model_from_json(json_string, custom_objects=custom_objects)
            elif arch_path.endswith('.yml') or arch_path.endswith('.yaml'):
                with open(arch_path) as fp:
                    yaml_string = fp.read()
                model = keras.models.model_from_yaml(yaml_string, custom_objects=custom_objects)
            else:
                raise ValueError('File type for architecture not recognized')
            model.load_weights(model_path)

        # Get the inputs of the model
        output.servable.methods['run'].input = output.format_layer_spec(model.input_shape)
        output.servable.methods['run'].output = output.format_layer_spec(model.output_shape)
        if output_names is not None:
            output.servable.methods['run'].method_details['classes'] = output_names

        # Get a full description of the model. Limit summary to _summary_limit in length
        _summary_tmp = []
        model.summary(print_fn=_summary_tmp.append)
        summary = "\n".join(_summary_tmp)
        summary = (summary[:_summary_limit] + '<<TRUNCATED>>') if len(summary) > _summary_limit else summary

        output.servable.model_summary = summary
        output.servable.model_type = 'Deep NN'

        # Add keras as a dependency
        keras_version = keras.__version__
        if not (keras_version.endswith("-tf") or use_tf_keras):
            output.add_requirement('keras', keras_version)
        output.add_requirement('h5py', 'detect')

        # Detect backend and get its version
        _detect_backend(keras, output)

        return output

    def format_layer_spec(self, layers) -> ArgumentTypeMetadata:
        """Make a description of a list of input or output layers

        Args:
            layers (tuple or [tuple]): Shape of the layers
        Return:
            (dict) Description of the inputs / outputs
        """
        if isinstance(layers, tuple):
            return ArgumentTypeMetadata.parse_obj(compose_argument_block("ndarray", "Tensor", shape=list(layers)))
        else:
            return ArgumentTypeMetadata.parse_obj(
                compose_argument_block("tuple", "Tuple of tensors",
                                       element_types=[self.format_layer_spec(i) for i in layers])
            )

    def add_custom_object(self, name, custom_object):
        """Add a custom layer to the model specification

        See `Keras FAQs
        <https://keras.io/getting-started/faq/#handling-custom-layers-or-other-custom-objects-in-saved-models>`
        for details.

        Args:
              name (string): Name of the custom object
              custom_object (class): Class of the custom object
        Return:
            self
        """

        # get the class name for the custom object
        object_name = custom_object.__name__
        module = custom_object.__module__

        # Add the layer to the model definition
        if 'custom_objects' not in self.servable.options:
            self.servable.options['custom_objects'] = {}
        self.servable.options['custom_objects'][name] = '{}.{}'.format(module, object_name)

    def _get_handler(self):
        return "keras.KerasServable"

    def _get_type(self):
        return "Keras Model"
