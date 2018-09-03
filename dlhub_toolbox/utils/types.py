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
