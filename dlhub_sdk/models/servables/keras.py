try:
    # Attempt to use regular keras first, as we figure it's installed for a reason
    import keras
except ImportError:
    from tensorflow import keras


from dlhub_sdk.models.servables.python import BasePythonServableModel
from dlhub_sdk.utils.types import compose_argument_block


keras_version = keras.__version__
_keras_version_tuple = tuple(int(i) for i in keras_version.rstrip("-tf").split("."))
_summary_limit = 10000


def _detect_backend(output):
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
                     custom_objects=None):
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
       """
        output = super(KerasModel, cls).create_model('predict')

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
        output['servable']['methods']['run']['input'] = output.format_layer_spec(model.input_shape)
        output['servable']['methods']['run']['output'] = output.format_layer_spec(
            model.output_shape)
        if output_names is not None:
            output['servable']['methods']['run']['method_details']['classes'] = output_names

        # Get a full description of the model. Limit summary to _summary_limit in length
        output.summary = ""

        def capture_summary(x):
            output.summary += x + "\n"

        model.summary(print_fn=capture_summary)
        output.summary = (output.summary[:_summary_limit] + '<<TRUNCATED>>') \
            if len(output.summary) > _summary_limit else output.summary

        output['servable']['model_summary'] = output.summary
        output['servable']['model_type'] = 'Deep NN'

        # Add keras as a dependency
        if not keras_version.endswith("-tf"):
            output.add_requirement('keras', keras_version)
        output.add_requirement('h5py', 'detect')

        # Detect backend and get its version
        _detect_backend(output)

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

    def add_custom_object(self, name, custom_layer):
        """Add a custom layer to the model specification

        See `Keras FAQs
        <https://keras.io/getting-started/faq/#handling-custom-layers-or-other-custom-objects-in-saved-models>`
        for details.

        Args:
              name (string): Name of the layer
              custom_layer (class): Class of the custom layer
        Return:
            self
        """

        # Get the class name for the custom layer
        layer_name = custom_layer.__name__
        if not issubclass(custom_layer, keras.layers.Layer):
            raise ValueError("Custom layer ({}) must be a subclass of Layer".format(layer_name))
        module = custom_layer.__module__

        # Add the layer to the model definition
        if 'options' not in self._output['servable']:
            self['servable']['options'] = {}
        if 'custom_objects' not in self['servable']['options']:
            self['servable']['options']['custom_objects'] = {}
        self['servable']['options']['custom_objects'][name] = '{}.{}'.format(module, layer_name)

    def _get_handler(self):
        return "keras.KerasServable"

    def _get_type(self):
        return "Keras Model"
