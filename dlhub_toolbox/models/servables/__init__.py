from dlhub_toolbox.models import BaseMetadataModel


class BaseServableModel(BaseMetadataModel):
    """Base class for servables"""

    def to_dict(self):
        output = super(BaseServableModel, self).to_dict()

        # Add the resource type
        #  I chose "InteractiveResource" as the point of DLHub is to provide
        #   web servies for interacting with these models ("query/response portals" are
        #   defined as "InteractiveResources") rather than downloading the source code
        #   (which would fit the definition of software)
        output['datacite']['resourceType'] = {'resourceTypeGeneral': 'InteractiveResource'}

        # Add the model running-information
        output['servable'] = {'run': {
            'handler': self._get_handler(),
            'input': self._get_input(),
            'output': self._get_output()
        }}

        return output

    def _get_handler(self):
        """Generate the name of the function being executed to run the servable

        Returns:
            (string) path to the python function (e.g., "application.run")
        """
        raise NotImplementedError()

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
