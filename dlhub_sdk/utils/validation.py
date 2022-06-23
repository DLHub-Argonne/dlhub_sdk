from io import IOBase
from logging import Logger
from typing import Any
from numpy import ndarray, ndenumerate

# warning message that is delivered when a boolean is (perhaps) incorrectly considered an integer
BOOL_SUB_INT_MSG = "[WARNING] Boolean input has been validated as type Integer, this is likely unintended."


def type_name_to_type(name: str) -> type:
    """Convert string type name to Python type object

    Args:
        name (string): The name of the type in question
    Returns:
        type: the type object whose __name__ is name (or None in the case of "None")
    Raises:
        TypeError: If name is not a string
        ValueError: If name is not matched to a type object
    """
    type_table = {"boolean": bool, "integer": int, "string": str, "file": IOBase, "ndarray": ndarray}

    try:
        return type_table.get(name) or __builtins__[name]
    except TypeError:
        raise TypeError(f"expected argument of type str, received: {type(name).__name__}")  # an easier error to understand than 'unhashable type'
    except KeyError:
        raise ValueError(f"received an unknown type name: {name}")


def validate(inputs: Any, db_entry: dict, *, logger: Logger = None) -> None:
    expected_input_type = type_name_to_type(db_entry["type"])

    validate_type(inputs, expected_input_type, logger=logger)

    if expected_input_type is list or expected_input_type is tuple:
        expected_item_type = type_name_to_type(db_entry["item_type"]["type"])
        validate_iterable(inputs, expected_item_type, logger=logger)

    elif expected_input_type is ndarray:
        expected_shape = tuple(db_entry["shape"])
        expected_item_type = type_name_to_type(db_entry["item_type"]["type"])
        validate_ndarray(inputs, expected_shape, expected_item_type, logger=logger)

    elif expected_input_type is dict:
        expected_properties = db_entry["properties"]
        validate_dict(inputs, expected_properties, logger=logger)


def validate_type(obj: Any, in_type: type, *, logger: Logger = None) -> None:  # better var name for in_type?
    """Compare the type of obj with in_type

    Args:
        obj (Any): The object whose type needs to be validated
        in_type (type): The type that obj is expected to have
        logger (Logger): Optionally output warnings through logger
    Returns:
        None
    Raises:
        TypeError: If the types do not match
    """
    log_func = print if logger is None else logger.warning

    if not isinstance(obj, in_type):
        raise TypeError(f"dl.run given improper input type: expected {in_type.__name__}, received {type(obj).__name__}")
    elif isinstance(obj, bool) and issubclass(int, in_type):
        log_func(BOOL_SUB_INT_MSG)


def validate_iterable(iterable: list | tuple, item_type: type, *, logger: Logger = None) -> None:
    """Compare the type of each item in iterable with item_type

    Args:
        iterable (list | tuple): The object whose items need to have their types validated
        item_type (type): The type that each item is expected to have
        logger (Logger): Optionally output warnings through logger
    Returns:
        None
    Raises:
        TypeError: If any of the items' types do not match
    """
    log_func = print if logger is None else logger.warning
    warn = True

    for i, item in enumerate(iterable):
        if not isinstance(item, item_type):
            raise TypeError(f"dl.run given improper input type: expected {type(iterable).__name__}[{item_type.__name__}], "
                            f"received {type(item).__name__} at index {i}")
        elif warn and isinstance(item, bool) and issubclass(int, item_type):
            log_func(BOOL_SUB_INT_MSG)
            warn = False


def validate_ndarray(arr: ndarray, shape: tuple, item_type: type, *, logger: Logger = None) -> None:
    """Compare the shape and type of each item in arr with shape and item_type, respectively

    Args:
        arr (ndarray): The ndarray whose shape and items need to be validated
        shape (tuple): The shape that arr is expected to have
        item_type (type): The type that each item in arr is expected to have
        logger (Logger): Optionally output warnings through logger
    Returns:
        None
    Raises:
        ValueError: If arr.shape does not match shape
        TypeError: If any of the items' types do not match
    """
    log_func = print if logger is None else logger.warning

    shape_err = ValueError(f"dl.run given improper input: expected ndarray.shape = {shape}, received shape: {arr.shape}")

    if len(arr.shape) != len(shape):
        raise shape_err
    elif not all(map(lambda t: t[0] == t[1] or t[1] == "None", zip(arr.shape, shape))):
        raise shape_err
    elif item_type:
        warn = True

        for i, item in ndenumerate(arr):
            if not isinstance(item, item_type):
                raise TypeError(f"dl.run given improper input type: expected ndarray[{item_type.__name__}], "
                                f"received {type(item).__name__} at index {i}")
            elif warn and isinstance(item, bool) and issubclass(int, item_type):
                log_func(BOOL_SUB_INT_MSG)
                warn = False


def validate_dict(dct: dict, props: dict, *, logger: Logger = None) -> None:
    """Recursively validate each of the inputs in dct against props

    Args:
        dct (dict): The dict whose keys and values need to be validated
        props (dict): The dict that describes the expected keys and values
        logger (Logger): Optionally output warnings through logger
    Returns:
        None
    Raises:
        ValueError: If dct is missing a key from props or a value in dct causes an error
        TypeError: If any of the values' types do not match
    """
    """ for key in dct:
        if key not in props:
            raise ValueError(f"dl.run given improper input: given unexpected dictionary key ({key})") """
    for key in props:
        if key not in dct:
            raise ValueError(f"dl.run given improper input: expected dictionary key ({key}) to be present")
        validate(dct[key], props[key], logger=logger)
