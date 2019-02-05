import pkg_resources
import importlib
import requests
import os


from dlhub_sdk.models import BaseMetadataModel


class BaseServableModel(BaseMetadataModel):
    """Base class for servables"""

    def __init__(self):
        super(BaseServableModel, self).__init__()

        # Add the resource type
        #  I chose "InteractiveResource" as the point of DLHub is to provide
        #   web servies for interacting with these models ("query/response portals" are
        #   defined as "InteractiveResources") rather than downloading the source code
        #   (which would fit the definition of software)
        self._output['datacite']['resourceType'] = {'resourceTypeGeneral': 'InteractiveResource'}

        # Define artifact type
        self._output['dlhub']['type'] = 'servable'

        # Initialize the model running-information
        self._output['servable'] = {
            'methods': {'run': {}},
            'shim': self._get_handler(),
            'type': self._get_type(),
            'dependencies': {'python': {}}
        }

    def _get_handler(self):
        """Generate the name of the servable class that DLHub will use to read this metadata

        Returns:
            (string) path to the python class (e.g., "python.PythonStaticMethod")
        """
        raise NotImplementedError()

    def _get_type(self):
        """Get a human-friendly name for this type of servable

        Returns:
            (string): Human-friendly name of an object
        """
        raise NotImplementedError()

    def register_function(self, name, inputs, outputs, parameters=None, method_details=None):
        """Registers a new function to this servable

        See :code:`compose_argument_type` utility function for how to define the inputs
        and outputs to this function.

        Args:
            name (string): Name of the function (e.g., "run")
            inputs (dict): Description of inputs to the function
            outputs (dict): Description of the outputs of the function
            parameters (dict): Any additional parameters for the function and their default values
            method_details (dict): Any options used when constructing a shim to run this function.
        """

        # Check defaults
        if method_details is None:
            method_details = {}
        if parameters is None:
            parameters = {}

        # Add the function
        self._output["servable"]["methods"][name] = {
            'input': inputs,
            'output': outputs,
            'parameters': parameters,
            'method_details': method_details
        }

        return self

    def to_dict(self, simplify_paths=False, save_class_data=False):
        # Make sure the inputs and outputs have been set
        if len(self._output["servable"]["methods"]["run"].get("input", {})) == 0:
            raise ValueError('Inputs have not been defined')
        if len(self._output["servable"]["methods"]["run"].get("output", {})) == 0:
            raise ValueError('Outputs have not been defined')

        return super(BaseServableModel, self).to_dict(simplify_paths)

    def add_requirement(self, library, version=None):
        """Add a required Python library.

        The name of the library should be either the name on PyPI, or a URL for the git repository
        holding the code (e.g., ``git+https://github.com/DLHub-Argonne/dlhub_sdk.git``)

        Args:
            library (string): Name of library
            version (string): Required version. 'latest' to use the most recent version on PyPi (if
                available). 'detect' will attempt to find the version of the library installed on
                the computer running this software. Default is ``None``
        """

        # Attempt to determine the version automatically
        if version == "detect":
            try:
                module = importlib.import_module(library)
                version = module.__version__
            except Exception:
                version = pkg_resources.get_distribution(library).version
        elif version == "latest":
            pypi_req = requests.get('https://pypi.org/pypi/{}/json'.format(library))
            version = pypi_req.json()['info']['version']

        # Set the requirements
        self._output["servable"]["dependencies"]["python"][library] = version
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

    def parse_repo2docker_configuration(self, directory=None):
        """Gathers information about required environment from repo2docker configuration files.

        See https://repo2docker.readthedocs.io/en/latest/config_files.html for more details

        Args:
            directory (str): Path to directory containing configuration files
                (default: current working directory)
        """

        # Get a list of all files
        config_files = ['environment.yml', 'requirements.txt', 'setup.py', 'REQUIRE', 'install.R',
                        'apt.txt', 'DESCRIPTION', 'manifest.xml', 'postBuild', 'start',
                        'runtime.txt', 'default.nix', 'Dockerfile']

        # Get the directory name if `None`
        if directory is None:
            directory = os.getcwd()

        # Add every file we can find
        for file in config_files:
            path = os.path.join(directory, file)
            if os.path.isfile(path):
                self.add_file(path)

        return self
