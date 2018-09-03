"""Tools to annotate generic operations (e.g., class method calls) in Python"""
from dlhub_toolbox.models.servables import BaseServableModel
import pickle as pkl
import pkg_resources
import requests


class BasePythonServableModel(BaseServableModel):
    """Describes a static python function to be run"""

    def __init__(self, method, function_kwargs=None):
        """Initialize a model for a python object

        Args:
            method (string): Name of the method for this class
            function_kwargs (dict): Names and values of any other argument of the function to set
                the values must be JSON serializable.
        """
        super(BasePythonServableModel, self).__init__()

        # Get default values
        if function_kwargs is None:
            function_kwargs = dict()

        # Set values
        self.method = method
        self.function_kwargs = function_kwargs
        self.requirements = {}

        # Initialize holders for inputs and outputs
        self.input = {}
        self.output = {}

    def add_requirement(self, library, version=None):
        """Add a required Python library.

        The name of the library should be either the name on PyPI, or a link to the

        Args:
            library (string): Name of library
            version (string): Required version. 'latest' to use the most recent version on PyPi (if
            available). 'detect' will attempt to find the version of the library installed on
                the computer running this software.
        """

        # Attempt to determine the version automatically
        if version == "detect":
            version = pkg_resources.get_distribution(library).version
        elif version == "latest":
            pypi_req = requests.get('https://pypi.org/pypi/{}/json'.format(library))
            version = pypi_req.json()['info']['version']

        # Set the requirements
        self.requirements[library] = version
        return self

    def add_requirements(self, requirements):
        """Add a dictionary of requirements

        Utility wrapper for `add_requirement`

        Args:
            requirements (dict): Keys are names of library (str), values are the version
        """
        for p, v in requirements.items():
            self.add_requirement(p, v)
        return self

    def set_inputs(self, data_type, description, shape=(), **kwargs):
        """Define the inputs to this function

        Args:
            data_type (string): Type of the input data
            description (string): Human-friendly description of the data
            shape (list): Required for data_type of list or ndarray. Use `None` for dimensions that
                can have any numbers of values
            kwargs (dict): Any other details particular to this kind of data
        """
        # Initialize the description
        self.input = {
            'type': data_type,
            'description': description
        }

        # Check that shape is specified if need be
        if data_type == "list" or data_type == "ndarray":
            if len(shape) == 0:
                raise ValueError('Shape must be specified for list-like data_types')
            self.input['shape'] = list(shape)

        # Add in any kwargs
        self.input.update(**kwargs)

        return self

    def set_outputs(self, data_type, description, shape=(), **kwargs):
        """Define the outputs to this function

        Args:
            data_type (string): Type of the output data
            description (string): Human-friendly description of the data
            shape (list): Required for data_type of list or ndarray. Use `None` for dimensions that
                can have any numbers of values
            kwargs (dict): Any other details particular to this kind of data
        """
        # Initialize the description
        self.output = {
            'type': data_type,
            'description': description
        }

        # Check that shape is specified if need be
        if data_type == "list" or data_type == "ndarray":
            if len(shape) == 0:
                raise ValueError('Shape must be specified for list-like data_types')
            self.output['shape'] = list(shape)

        # Add in any kwargs
        self.output.update(**kwargs)

        return self

    def _get_input(self):
        if len(self.input) == 0:
            raise ValueError('Inputs have not been defined')
        return self.input

    def _get_output(self):
        if len(self.output) == 0:
            raise ValueError('Outputs have not been defined')
        return self.output

    def to_dict(self):
        # Get the higher level
        output = super(BasePythonServableModel, self).to_dict()

        # Add Python settings
        output['servable'].update({
            'langugage': 'python',
            'method_details': {
                'method_name': self.method,
                'default_args': self.function_kwargs
            },
            'dependencies': {'python': self.requirements}
        })

        return output


class PickledClassServableModel(BasePythonServableModel):
    """Model for describing servables where the function to be performed is a method of a class.

    To use this model, you must define the path to the pickled object and the function of that
    object to be called. Any additional libraries (beyond the standard libraries) required
    to run the library and their versions must also be specified. You may also specify
    any arguments of the class that should be set as defaults."""

    def __init__(self, path, method, function_kwargs=None):
        """Initialize a model for a python object

        Args:
            path (string): Path to a pickled Python file
            method (string): Name of the method for this class
            function_kwargs (dict): Names and values of any other argument of the function to set
                the values must be JSON serializable.
        """
        super(PickledClassServableModel, self).__init__(method, function_kwargs)

        self.path = path

        # Get the class name
        with open(self.path, 'rb') as fp:
            self.class_name = pkl.load(fp).__class__.__name__

    def _get_handler(self):
        return 'python_shim.run_class_method'

    def list_files(self):
        return [self.path]

    def to_dict(self):
        output = super(PickledClassServableModel, self).to_dict()

        # Add pickle-specific options
        output['servable']['type'] = 'pickled_class'
        output['servable']['location'] = self.path
        output['servable']['method_details']['class_name'] = self.class_name

        return output


class PythonStaticMethodModel(BasePythonServableModel):
    """Model for a servable that calls a Python static method. Static methods can be called
    without any other context, unlike the class methods in PickledClassServableModelBase.

    An example static method is the sqrt operation from numpy, `numpy.sqrt`. You can make a model
    of this function by calling :code:`PythonStaticMethodModel.from_function_pointer(numpy.sqrt)`.
    """

    def __init__(self, module, method, autobatch=False, function_kwargs=None):
        """Initialize the method

        Args:
            module (string): Name of the module holding the function
            method (string): Name of the method for this class
            autobatch (bool): Whether to automatically run this function on a list of inputs.
                Calls :code:`map(f, list)`
            function_kwargs (dict): Names and values of any other argument of the function to set
                the values must be JSON serializable.
        """
        super(PythonStaticMethodModel, self).__init__(method, function_kwargs)

        self.module = module
        self.autobatch = autobatch

    @classmethod
    def from_function_pointer(cls, f, autobatch=False, function_kwargs=None):
        """Construct the module given a function pointer

        Args:
            f (object): A function pointer
            autobatch (bool): Whether to run function on an interable of entries
            function_kwargs (dict): Any default options for this function
        """
        return cls(f.__module__, f.__name__, autobatch, function_kwargs)

    def _get_handler(self):
        return 'python_shim.run_static_method'

    def to_dict(self):
        output = super(PythonStaticMethodModel, self).to_dict()

        output['servable']['type'] = 'py_static_method'
        output['servable']['method_details']['module'] = self.module
        output['servable']['method_details']['autobatch'] = self.autobatch

        return output

    def list_files(self):
        return []
