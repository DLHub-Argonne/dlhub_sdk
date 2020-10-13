"""Utilities for generating descriptions of data types"""
from six import string_types


def simplify_numpy_dtype(dtype):
    """Given a numpy dtype, write out the type as string

    Args:
        dtype (numpy.dtype): Type
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


def compose_argument_block(data_type, description, shape=None, item_type=None,
                           python_type=None, properties=None, element_types=None, **kwargs):
    """Compile a list of argument descriptions into an argument_type block

    Args:
        data_type (string): Type of the input data
        description (string): Human-friendly description of the data
        shape (list): Required for data_type of list or ndarray. Use `None` for dimensions that
            can have any numbers of values
        item_type (string/dict): Description of the item type. Required for data_type = list.
            Can either be a string type, or a dict that is a valid type for an argument type block
        python_type (string): Full path of a Python object type
            (e.g., :code:`pymatgen.core.Compostion`)
        properties (dict): Descriptions of the types in a dictionary
        element_types ([dict] or [str]): Types of elements in a tuple. List of type definition
            dictionaries or types as strings.
    Keyword Arguments: Any other details particular to this kind of data
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
        if shape is None:
            raise ValueError('Shape must be specified for ndarrays')
        args['shape'] = list(shape)

    # Check if the item_type needs to be defined
    if data_type == "list":
        if item_type is None:
            raise ValueError('Item type must be defined for lists')

    # Check if the element_type need be defined
    if data_type == "tuple":
        if element_types is None:
            raise ValueError('Element type must be defined for tuples')

    # If the type is "python object", python_type must be specified
    if data_type == "python object":
        if python_type is None:
            raise ValueError('Python type must be defined ')
        args['python_type'] = python_type

    # Check if the keys need to be defined
    if data_type == "dict":
        if properties is None:
            raise ValueError('Properties must be defined for dict type')
        args['properties'] = properties

    # Define the item types
    if item_type is not None:
        if isinstance(item_type, dict):
            args['item_type'] = item_type
        elif isinstance(item_type, string_types):  # Is a string
            args['item_type'] = {'type': item_type}

    # Define the types of tuples
    if element_types is not None:
        args['element_types'] = list(element_types)

    # Add in any kwargs
    args.update(**kwargs)
    return args
