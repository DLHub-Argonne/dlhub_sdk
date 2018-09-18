from dlhub_toolbox.models import BaseMetadataModel


class BaseServableModel(BaseMetadataModel):
    """Base class for servables"""

    def to_dict(self, simplify_paths=False):
        output = super(BaseServableModel, self).to_dict(simplify_paths)

        # Add the resource type
        #  I chose "InteractiveResource" as the point of DLHub is to provide
        #   web servies for interacting with these models ("query/response portals" are
        #   defined as "InteractiveResources") rather than downloading the source code
        #   (which would fit the definition of software)
        output['datacite']['resourceType'] = {'resourceTypeGeneral': 'InteractiveResource'}

        # Add the model running-information
        output['servable'] = {
            'methods': {'run': {
                'input': self._get_input(),
                'output': self._get_output(),
                'parameters': self._get_parameters(),
                'method_details': self._get_method_details(),
            }},
            "shim": self._get_handler()}

        return output

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

    def _get_input(self):
        """Generate a listing of the desired inputs to an ML model

        Returns:
            (dict) Description of the model inputs, required keys:
                - type: Category of input (e.g., 'Python object', 'ndarray', 'list')
                - description: Human-friendly descriptio of the model
                - shape: Shape of the array, for list-like inputs
                - items: Type of the items in the list
        """
        raise NotImplementedError()

    def _get_output(self):
        """Generate a listing of the outputs for a model

        Returns:
            (dict) Description of the model inputs, required keys:
                - type: Category of input (e.g., 'Python object', 'ndarray', 'list')
                - description: Human-friendly descriptio of the model
                - shape: Shape of the array, for list-like inputs
                - items: Type of the items in the list
        """
        raise NotImplementedError()

    def _get_parameters(self):
        """Generate a dictionary of parameters of the function and their default values

        Returns:
            (dict) Default parameters for the servable
        """
        raise NotImplementedError()

    def _get_method_details(self):
        """Generate any special options used to construct the servable.
        In contrast to the parameters, these options are only used when constructing the servable
        and not on every invocation.
        """
        raise NotImplementedError()
