"""Utilities for generating descriptions of data types"""


def simplify_numpy_dtype(dtype):
    """Given a numpy dtype, write out the type as string

    Args:
        dtype (numpy.dytpe): Type
    Returns:
        (string) name as a simple string
    """

    kind = dtype.kind
    if kind == "b":
        return "boolean"
    elif kind == "i" or kind == "u":
        return "integer"
    elif kind == "f":
        return "float"
    elif kind == "c":
        return "complex"
    elif kind == "m":
        return "timedelta"
    elif kind == "M":
        return "datetime"
    elif kind == "S" or kind == "U":
        return "string"
    else:
        return "python object"


def compose_argument_block(data_type, description, shape=(), item_type=None, **kwargs):
    """Compile a list of argument descriptions into an argument_type block

    Args:
        Args:
        data_type (string): Type of the input data
        description (string): Human-friendly description of the data
        shape (list): Required for data_type of list or ndarray. Use `None` for dimensions that
            can have any numbers of values
        item_type (string/dict): Description of the item type. Required for data_type = list.
            Can either be a string type, or a dict that is a valid type for an argument type block
        kwargs (dict): Any other details particular to this kind of data
    Returns:
        (dict) Description of method in a form compatible with DLHub
    """
    # Initialize the description
    args = {
        'type': data_type,
        'description': description
    }

    # Check that shape is specified if need be
    if data_type == "ndarray":
        if len(shape) == 0:
            raise ValueError('Shape must be specified for ndarrays')
        args['shape'] = list(shape)

    # Check if the item_type needs to be defined
    if data_type == "list":
        if item_type is None:
            raise ValueError('Item type must be defined for lists')

    # Define the item types
    if item_type is not None:
        if isinstance(item_type, dict):
            args['item_type'] = item_type
        else:  # Is a string
            args['item_type'] = {'type': item_type}

    # Add in any kwargs
    args.update(**kwargs)
    return args
