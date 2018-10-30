import importlib


def unserialize_object(data):
    """Given a metadata dictionary object, form a MetadataModel class

    Args:
        data (dict): Metadata to unserialize
    Returns:
        (BaseMetadataModel) Unserialized object
    """

    # Get the class to be loaded
    #   Assume the base class if '@class' not present
    class_name = data.get('@class', 'dlhub_sdk.models.BaseMetadataModel')

    # Make sure it is from the correct package
    if not class_name.startswith('dlhub_sdk.models.'):
        raise AttributeError('Metadata class must be from the `dlhub_sdk.models package')

    # Get the desired metadata class
    components = class_name.split(".")
    module_name = ".".join(components[:-1])
    mod = importlib.import_module(module_name)
    output = getattr(mod, components[-1])

    # Instantiate it using the user-provided data
    return output.from_dict(data)
