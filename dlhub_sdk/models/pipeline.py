"""Model for a pipeline of several servables"""
from dlhub_sdk.models import BaseMetadataModel


class PipelineModel(BaseMetadataModel):
    """Model for a pipeline of several servables

    A Pipeline is created after individual servables have been published in DLHub, or at least
    assigned a DLHub identifier. A Pipeline is formed from a list of these servables, and any
    options to employ when running them. A step in a pipeline could also be another pipeline.

    A simple example for a DLHub pipeline is an image classification tool. The first step in the
    pipeline is an image reader take takes any image type and produces an array. The second step
    standardizes the shape of the image, where the "options" to the servable are the desired
    resolution and whether the image is grayscale or not. The final step is the classification
    pipeline. Put together, the image pipeline can support any type of input data.
    """

    def __init__(self):
        super(PipelineModel, self).__init__()

        # Make as a "InteractiveResource"
        self['datacite']['resourceType'] = {'resourceTypeGeneral': 'InteractiveResource'}

        # Add list of pipeline steps
        self._output['pipeline'] = {'steps': []}

        # Define artifact type
        self._output['dlhub']['type'] = 'pipeline'

    def add_step(self, author, name, description, parameters=None):
        """Add a step to the pipeline

        Args:
            author (string): DLHub username of the owner of the servable
            name (string): Name of the DLHub servable
            description (string): A short description of this step
            parameters (dict): Any options for the servable.
                See the list of parameters for a servable
        """

        # Compose the block
        step = {
            'author': author,
            'name': name,
            'description': description
        }
        if parameters is not None:
            step['parameters'] = parameters
        self["pipeline"]["steps"].append(step)
