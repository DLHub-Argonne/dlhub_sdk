from typing import Dict, Optional, List, Any, Union

from pydantic import BaseModel, Field

from dlhub_sdk.models import BaseMetadataModel


class ArgumentTypeMetadata(BaseModel):
    """Description of an input argument"""

    type: str = Field(None, help="Type of the argument")
    description: Optional[str] = Field(None, help="Description of the argument")
    shape: Optional[List[Union[None, int]]] = None
    python_type: Optional[str] = None
    item_type: Optional['ArgumentTypeMetadata'] = None
    element_types: Optional[List['ArgumentTypeMetadata']] = None
    properties: Optional[Dict[str, 'ArgumentTypeMetadata']] = None


ArgumentTypeMetadata.update_forward_refs()


class MethodMetadata(BaseModel):
    """Metadata that describes each method"""

    input: ArgumentTypeMetadata = Field(..., help="Description of the method inputs")
    output: ArgumentTypeMetadata = Field(..., help="Description of the method outputs")
    parameters: Dict[str, Any] = Field(default_factory=dict, help="Description of method runtime parameters")
    method_details: Dict = Field(default_factory=dict, help="Options used to construct the method in DLHub.")


class ServableMetadata(BaseModel):
    """Metadata for servable objects.

    Captures the information that describe how to run a servable."""

    type: Optional[str] = Field(None, help="Type of the servable. Meant to be human readable")
    shim: Optional[str] = Field(None, help="Name of the home_run shim used to run a servable.")
    model_type: Optional[str] = Field(None, help="Simple description of the type of a machine learning model")
    model_summary: Optional[str] = Field(None, help="Longer-form description of a model.")
    methods: Dict[str, MethodMetadata] = Field(default_factory=dict,
                                               help="Description of each method for the servable")
    options: Optional[Dict] = Field(default_factory=dict, help="Settings used to construct the servable")

    class Config:
        extra = 'allow'


class BaseServableModel(BaseMetadataModel):
    """Base class for servables. Holds the metadata for the object and how to create and run the servable object."""

    servable: ServableMetadata = Field(ServableMetadata,
                                       help="Metadata describing how to construct and run a servable")

    def __init__(self):
        super(BaseServableModel, self).__init__()

        # Add the resource type
        #  I chose "InteractiveResource" as the point of DLHub is to provide
        #   web servies for interacting with these models ("query/response portals" are
        #   defined as "InteractiveResources") rather than downloading the source code
        #   (which would fit the definition of software)
        self.datacite.resourceType = {'resourceTypeGeneral': 'InteractiveResource'}

        # Define artifact type
        self.dlhub.type = 'servable'

        # Initialize the model running-information
        self.servable = ServableMetadata(shim=self._get_handler(), type=self._get_type())

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
        self.servable.methods[name] = MethodMetadata.parse_obj({
            'input': inputs,
            'output': outputs,
            'parameters': parameters,
            'method_details': method_details
        })

        return self
