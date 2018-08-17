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
        output['datacite']['resourceType'] = 'InteractiveResource'

        return output
