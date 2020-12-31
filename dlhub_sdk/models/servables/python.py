"""Tools to annotate generic operations (e.g., class method calls) in Python"""
import pickle as pkl

from dlhub_sdk.models.servables import BaseServableModel, ArgumentTypeMetadata
from dlhub_sdk.utils.types import compose_argument_block


class BasePythonServableModel(BaseServableModel):
    """Describes a static python function to be run"""

    def set_unpack_inputs(self, x, method_name='run'):
        """Define whether the inputs need to be unpacked before executing the function

        Set to `true` if the function takes more than one input. Otherwise, the default is `False`

        Args:
            x (bool): Desired setting
            method_name (str): Name of the method to modify
        Returns:
            (BasePythonServableModel): self
        """

        if self.servable.methods[method_name].input.type not in ['list', 'tuple']:
            raise ValueError('Only "list" and "tuple" inputs are compatible with unpacking')
        self.servable.methods[method_name].method_details['unpack'] = x
        return self

    @classmethod
    def create_model(cls, method, function_kwargs=None) -> 'BasePythonServableModel':
        """Initialize a model for a python object

        Args:
            method (string): Name of the method for this class
            function_kwargs (dict): Names and values of any other argument of the function to set
                the values must be JSON serializable.
        """
        output = cls()

        # Get default values
        if function_kwargs is None:
            function_kwargs = dict()

        # Set values
        output.register_function("run", {}, {}, function_kwargs, {'method_name': method})
        return output

    def set_inputs(self, data_type, description, shape=(), item_type=None, **kwargs):
        """Define the inputs to the default ("run") function

        Args:
            data_type (string): Type of the input data
            description (string): Human-friendly description of the data
            shape (list): Required for data_type of list or ndarray. Use `None` for dimensions that
                can have any numbers of values
            item_type (string/dict): Description of the item type. Required for data_type = list
        """
        args = compose_argument_block(data_type, description, shape, item_type, **kwargs)

        # Set the inputs
        self.servable.methods["run"].input = ArgumentTypeMetadata.parse_obj(args)
        return self

    def set_input_description(self, description, method='run'):
        """Set the human-readable description for this servable's inputs

        This method can be called when implementing a Keras, PyTorch, etc. servable to fill in
        an empty input description.

        Args:
            description (string): Human-readable description of the servable's inputs
            method (string): Name of the servable method to apply description to (by default, 'run')
        """

        self.servable.methods[method].input.description = description
        return self

    def set_output_description(self, description, method='run'):
        """Set the human-readable description for this servable's inputs

        This method can be called when implementing a Keras, PyTorch, etc. servable to fill in
        an empty input description.

        Args:
            description (string): Human-readable description of the servable's inputs
            method (string): Name of the servable method to apply description to (by default, 'run')
        """

        self.servable.methods[method].output.description = description
        return self

    def set_outputs(self, data_type, description, shape=(), item_type=None, **kwargs):
        """Define the outputs to the default ("run") function

        Args:
            data_type (string): Type of the output data
            description (string): Human-friendly description of the data
            shape (list): Required for data_type of ndarray. Use `None` for dimensions that
                can have any numbers of values
            item_type (string): Description of the type of item in a list
        """

        args = compose_argument_block(data_type, description, shape, item_type, **kwargs)
        self.servable.methods["run"].output = ArgumentTypeMetadata.parse_obj(args)
        return self


class PythonClassMethodModel(BasePythonServableModel):
    """Model for describing servables where the function to be performed is a method of a class.

    To use this model, you must define the path to the pickled object and the function of that
    object to be called. Any additional libraries (beyond the standard libraries) required
    to run the library and their versions must also be specified. You may also specify
    any arguments of the class that should be set as defaults."""

    @classmethod
    def create_model(cls, path, method, function_kwargs=None) -> 'PythonClassMethodModel':
        """Initialize a model for a python object

        Args:
            path (string): Path to a pickled Python file
            method (string): Name of the method for this class
            function_kwargs (dict): Names and values of any other argument of the function to set
                the values must be JSON serializable.
        """
        output = super(PythonClassMethodModel, cls).create_model(method, function_kwargs)

        output.add_file(path, 'pickle')

        # Get the class name
        with open(path, 'rb') as fp:
            obj = pkl.load(fp)
            class_name = '{}.{}'.format(obj.__class__.__module__, obj.__class__.__name__)

        output.servable.methods["run"].method_details.update({
            'class_name': class_name
        })

        return output

    def _get_handler(self):
        return 'python.PythonClassMethodServable'

    def _get_type(self):
        return 'Python class method'


class PythonStaticMethodModel(BasePythonServableModel):
    """Model for a servable that calls a Python static method. Static methods can be called
    without any other context, unlike the class methods in PickledClassServableModelBase.

    An example static method is the sqrt operation from numpy, `numpy.sqrt`. You can make a model
    of this function by calling :code:`PythonStaticMethodModel.from_function_pointer(numpy.sqrt)`.
    """

    @classmethod
    def create_model(cls, module, method, autobatch=False, function_kwargs=None):
        """Initialize the method

        Args:
            module (string): Name of the module holding the function
            method (string): Name of the method for this class
            autobatch (bool): Whether to automatically run this function on a list of inputs.
                Calls :code:`map(f, list)`
            function_kwargs (dict): Names and values of any other argument of the function to set
                the values must be JSON serializable.
        """
        output = super(PythonStaticMethodModel, cls).create_model(method, function_kwargs)

        output.servable.methods["run"].method_details.update({
            'module': module,
            'autobatch': autobatch
        })
        return output

    @classmethod
    def from_function_pointer(cls, f, autobatch=False, function_kwargs=None):
        """Construct the module given a function pointer

        Args:
            f (object): A function pointer
            autobatch (bool): Whether to run function on an iterable of entries
            function_kwargs (dict): Any default options for this function
        """
        return cls.create_model(f.__module__, f.__name__, autobatch, function_kwargs)

    def _get_handler(self):
        return 'python.PythonStaticMethodServable'

    def _get_type(self):
        return 'Python static method'
