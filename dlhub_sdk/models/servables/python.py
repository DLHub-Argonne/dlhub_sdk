"""Tools to annotate generic operations (e.g., class method calls) in Python"""
import pickle as pkl
import importlib
from inspect import Signature
from typing import Any, Dict, List, Tuple, Union
from numpy import ndarray

from dlhub_sdk.models.servables import BaseServableModel, ArgumentTypeMetadata
from dlhub_sdk.utils.types import compose_argument_block, PY_TYPENAME_TO_JSON


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
    def create_model(cls, path, method, function_kwargs=None, *, auto_inspect=False) -> 'PythonClassMethodModel':
        """Initialize a model for a python object

        Args:
            path (string): Path to a pickled Python file
            method (string): Name of the method for this class
            function_kwargs (dict): Names and values of any other argument of the function to set
                the values must be JSON serializable.
            auto_inspect (boolean): Whether or not to attempt to automatically extract inputs from the function
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

        if auto_inspect:
            func = getattr(obj, method)

            output = _add_extracted_metadata(func, output)

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
    def create_model(cls, module=None, method=None, autobatch=False, function_kwargs=None, *, f=None, auto_inspect=False):
        """Initialize the method based on the provided arguments

        Args:
            module (string): Name of the module holding the function
            method (string): Name of the method for this class
            autobatch (bool): Whether to automatically run this function on a list of inputs.
                Calls :code:`map(f, list)`
            function_kwargs (dict): Names and values of any other argument of the function to set
                the values must be JSON serializable.
            f (object): function pointer to the desired python function
            auto_inspect (boolean): Whether or not to attempt to automatically extract inputs from the function
        Raises:
            TypeError: If there is no valid way to process the given arguments
        """
        # if a pointer is provided, get the module and method
        if f is not None:
            module, method = f.__module__, f.__name__
            func = f
        # if it is not, ensure both the module and method are provided and get the function pointer
        elif module is not None and method is not None:
            module_obj = importlib.import_module(module)
            func = getattr(module_obj, method)
        else:
            raise TypeError("PythonStaticMethodModel.create_model was not provided valid arguments. Please provide either a funtion pointer"
                            " or the module and name of the desired static function")

        output = super(PythonStaticMethodModel, cls).create_model(method, function_kwargs)

        output.servable.methods["run"].method_details.update({
            'module': module,
            'autobatch': autobatch
        })

        if auto_inspect:
            output = _add_extracted_metadata(func, output)

        return output

    @classmethod
    def from_function_pointer(cls, f, autobatch=False, function_kwargs=None):
        """Construct the module given a function pointer
        Args:
            f (object): A function pointer
            autobatch (bool): Whether to run function on an iterable of entries
            function_kwargs (dict): Any default options for this function
        """
        return cls.create_model(f=f, autobatch=autobatch, function_kwargs=function_kwargs)

    def _get_handler(self):
        return 'python.PythonStaticMethodServable'

    def _get_type(self):
        return 'Python static method'


def _signature_to_input(sig: Signature) -> Dict[str, Any]:
    """Use a function signature to generate the input to set_inputs()"""
    if len(sig.parameters.values()) == 0:
        return {"data_type": "python object", "description": "", "python_type": "builtins.NoneType"}  # mirros last clause of _type_hint_to_metadata

    metadata = []
    for param in sig.parameters.values():
        # if the parameter is not type hinted, auto-extraction cannot proceed
        if param.annotation is param.empty:
            raise TypeError(f"Please provide a type hint for the parameter: {param.name}")
        # if the parameter is an iterable and its element type(s) were not provided, auto-extraction cannot proceed
        # this condition is sufficient because a proper type hint of such a type will be a GenericAlias and not the type itself
        elif param.annotation in {list, tuple}:  # dict could be included, but those values are unused in _type_hint_to_metadata as of now
            raise TypeError(f"Please provide the type(s) that the parameter: {param.name} is expected to accept")

        metadata.append(_type_hint_to_metadata(param.annotation))

    if len(metadata) == 1:
        metadata = metadata[0]  # get the item from the single item list
        return {"data_type": metadata.pop("type"), **metadata}  # change the name of the "type" property and merge the rest in

    return {"data_type": "tuple", "description": "", "element_types": metadata}


def _signature_to_output(sig: Signature) -> Dict[str, Any]:
    """Use a function signature to generate the input to set_outputs()"""
    # if the return value is not type hinted, auto-extraction cannot proceed
    if sig.return_annotation is sig.empty:
        raise TypeError("Please provide a type hint for the return type of your function")
    if sig.return_annotation in {list, tuple}:  # dict could be included, but those values are unused in _type_hint_to_metadata as of now
        raise TypeError("Please provide the type(s) of elements in the return type hint")

    metadata = _type_hint_to_metadata(sig.return_annotation)

    return {"data_type": metadata.pop("type"), **metadata}  # change the name of the "type" property and merge the rest in


def _type_hint_to_metadata(hint: Union[Tuple, List, Dict, type]) -> Dict[str, str]:
    """Take a type hint and convert it into valid DLHub metadata
    Args:
        hint (type hint | type): a type hint can be either a type (e.g. int) or a GenericAlias (e.g. list[int]),
                                 these objects are retrieved from Signature object properties
    Returns:
        (dict): the metadata for the given hint
    """
    if hasattr(hint, "__origin__"):  # differentiates type hint objects from others
        # in a type hint, the __origin__ is the outer type (e.g. list in list[int])
        # and the inner type, int, would be at __args__[0]
        if hint.__origin__ is ndarray:
            return compose_argument_block("ndarray", "", shape="Any", item_type=_type_hint_to_metadata(hint.__args__[0]))
        elif hint.__origin__ is list:
            return compose_argument_block("list", "", item_type=_type_hint_to_metadata(hint.__args__[0]))  # __args__ is a tuple even if it's length 1
        elif hint.__origin__ is tuple:
            return compose_argument_block("tuple", "", element_types=[_type_hint_to_metadata(x) for x in hint.__args__])
        elif hint.__origin__ is dict:
            return compose_argument_block("dict", "", properties={})  # without the keys no part of the hint can be properly processed
        else:
            raise TypeError("Fatal error: unknown paramaterized type encountered")
    else:
        if hint is ndarray:
            return compose_argument_block("ndarray", "", shape="Any")

        json_name = PY_TYPENAME_TO_JSON.get(hint)
        if json_name:
            return compose_argument_block(json_name, "")

        if hint is None:
            hint = type(None)
        return compose_argument_block("python object", "", python_type=f"{hint.__module__}.{hint.__qualname__}")


def _add_extracted_metadata(func, model: BasePythonServableModel) -> BasePythonServableModel:
    """Helper function for adding generated input/output metadata to a model object
    Args:
        func: a pointer to the function whose data is to be extracted
        model (BasePythonServableModel): the model who needs its data to be updated
    Returns:
        (BasePythonServableModel): the model that was given after it is updated
    """
    sig = Signature.from_callable(func)
    model = model.set_inputs(**_signature_to_input(sig))
    model = model.set_outputs(**_signature_to_output(sig))
    return model
