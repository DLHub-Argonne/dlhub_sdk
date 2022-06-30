from io import IOBase
from pathlib import Path
from typing import Union, Any
from numpy import array, ndarray, ndenumerate
import warnings


class ValidationWarning(RuntimeWarning):
    """Brought to the user's attention when a validation step has dubious accuracy"""


def _type_name_to_type(name: str) -> type:
    """Convert string type name to Python type object

    Args:
        name (string): The name of the type in question
    Returns:
        type: the type object whose __name__ is name (or None in the case of "None")
    Raises:
        ValueError: If name is not matched to a type object
    """
    type_table = {"boolean": bool, "integer": int, "string": str, "file": Union[IOBase, Path, str], "ndarray": ndarray}

    try:
        return type_table.get(name) or __builtins__[name]  # getattr(__builtins__, name) if __builtins__ is a module
    except KeyError:  # AttributeError if __builtins__ is a module
        raise ValueError(f"found an unknown type name in servable metadata: {name}")


def _generate_err(err_type: Exception, path: list, expected: type = None, given: type = None, *, msg: str = None) -> Exception:
    """Generate an error based on the given arguments

    Args:
        err_type (Exception): The error type to generate
        path (list): List that stores the path through the data to display
        expected (type): What type the caller was expecting
        given (type): What type the caller received
        msg (string): The message to pass through to the generated error
    Returns:
        Exception
    """
    if expected is not None:
        expected = expected.__name__
    if given is not None:
        given = given.__name__
    loc = " at input" if path else ""

    for jump in reversed(path):
        expected = f"{jump[0]}[{expected}]"
    for jump in path:
        loc += f"[{repr(jump[1])}]"

    if msg:
        return err_type(msg.format(loc=loc))  # allows callers (never the user) to use "{loc}" to access the variable in this scope
    return err_type(f"dl.run given improper input type: expected {expected}, received {given}{loc}")


def validate(inputs: Any, db_entry: dict, path: list = None) -> None:
    """Perform the complete validation step

    Args:
        inputs (Any): The input that will be provided to a servable
        db_entry (dict): The metadata that inputs is validated against
        path (list): List that stores the path through the data to the current point
    Returns:
        None
    Raises:
        ValueError: If any value in inputs does not match the db_entry
        TypeError: If any type in inputs does not match the db_entry
    """
    path = [] if path is None else path

    expected_input_type = _type_name_to_type(db_entry["type"])
    _validate_type(inputs, expected_input_type, path)

    if expected_input_type is list:
        _validate_list(inputs, db_entry, path)

    elif expected_input_type is tuple:
        _validate_tuple(inputs, db_entry["element_types"], path)

    elif expected_input_type is ndarray:
        _validate_ndarray(inputs, db_entry["shape"], db_entry, path)

    elif expected_input_type is dict:
        _validate_dict(inputs, db_entry["properties"], path)
    # it is intentional that nothing is done in the absence of an Exception


def _validate_type(obj: Any, in_type: type, path: list) -> None:
    """Compare the type of obj with in_type

    Args:
        obj (Any): The object whose type needs to be validated
        in_type (type): The type that obj is expected to have
        path (list): List that stores the path through the data to the current point
    Returns:
        None
    Raises:
        TypeError: If the types do not match
    """
    obj_type = None if obj is None else type(obj)

    if not isinstance(obj, in_type):
        raise _generate_err(TypeError, path, in_type, obj_type)
    if isinstance(obj, bool) and issubclass(int, in_type):
        # warning message is delivered when a boolean is (perhaps) incorrectly considered an integer
        warnings.warn("Boolean input has been validated as type Integer, this is likely unintended.", ValidationWarning, stacklevel=2)


def _validate_list(li: list, db_entry: dict, path: list) -> None:
    """Recursively validate each of the elements in li against db_entry["item_type"]

    Args:
        li (list): The list whose items need to have their type validated
        db_entry (dict): The entry that stores type data for li
        path (list): List that stores the path through the data to the current point
    Returns:
        None
    Raises:
        TypeError: If any of the items' types do not match
    """
    path.append(["list", None])
    for i, item in enumerate(li):
        path[-1][1] = i
        validate(item, db_entry["item_type"], path)
    path.pop()


def _validate_tuple(tup: tuple, db_entries: list, path: list) -> None:
    """Recursively validate each of the elements in tup against the corresponding entry in db_entries

    Args:
        tup (tuple): The tuple whose items need to have their type validated
        db_entries (list): The list of dicts that store the metadata for each item in tup
        path (list): List that stores the path through the data to the current point
    Returns:
        None
    Raises:
        ValueError: If the number of entries and tuple elements do not match
        TypeError: If any of the items' types do not match
    """
    if len(tup) != len(db_entries):
        raise _generate_err(ValueError, path, msg=f"dl.run expected tuple of length {len(db_entries)}, recieved tuple with length {len(tup)}"
                                                  + "{loc}")

    path.append(["tuple", None])
    for i, (given, expected) in enumerate(zip(tup, db_entries)):
        path[-1][1] = i
        validate(given, expected, path)
    path.pop()


def _validate_ndarray(arr: ndarray, shape: list, db_entry: dict, path: list) -> None:
    """Compare the shape of arr with shape and recursively validate each of the elements in arr against db_entry["item_type"]

    Args:
        arr (ndarray): The ndarray whose shape and items need to be validated
        shape (list): The shape that arr is expected to have
        db_entry (dict): The entry where type data may or may not be retrieved
        path (list): List that stores the path through the data to the current point
    Returns:
        None
    Raises:
        ValueError: If arr.shape does not match shape
        TypeError: If any of the items' types do not match
    """
    shape = tuple(int(x) if x != "None" else x for x in shape)
    shape_err = _generate_err(ValueError, path, msg=f"dl.run given improper input: expected ndarray.shape = {shape}, received shape: {arr.shape}"
                                                    + "{loc}")

    if len(arr.shape) != len(shape):
        raise shape_err
    if not all(map(lambda t: t[0] == t[1] or t[1] == "None", zip(arr.shape, shape))):
        raise shape_err

    entry = db_entry.get("item_type")
    if entry:
        path.append(["ndarray", None])
        for i, item in ndenumerate(arr):
            path[-1][1] = i
            validate(item.item(), entry, path)
        path.pop()


def _validate_dict(dct: dict, props: dict, path: list) -> None:
    """Recursively validate each of the pairs in dct against props

    Args:
        dct (dict): The dict whose keys and values need to be validated
        props (dict): The dict that describes the expected keys and values
        path (list): List that stores the path through the data to the current point
    Returns:
        None
    Raises:
        ValueError: If dct is missing a key from props or a value in dct causes an error
        TypeError: If any of the values' types do not match
    """
    if props:
        path.append(["dict", None])
        for key in dct:
            path[-1][1] = key
            if key not in props:
                raise _generate_err(ValueError, path, msg=f"dl.run given improper input: given unexpected dictionary key: {repr(key)}"+"{loc}")
        for key in props:
            path[-1][1] = key
            if key not in dct:
                raise _generate_err(ValueError, path, msg=f"dl.run given improper input: expected dictionary key: {repr(key)} to be present"+"{loc}")
            validate(dct[key], props[key], path)
        path.pop()


def _test() -> None:
    metadata = [
        {"type": "integer"},
        {"type": "float"},
        {"type": "boolean"},
        {"item_type": {"type": "integer"}, "type": "list"},
        {"element_types": [{"type": "integer"}, {"type": "integer"}, {"type": "string"}], "type": "tuple"},
        {"properties": {"a": {"type": "integer"}, "b": {"type": "integer"}, "c": {"type": "integer"}}, "type": "dict"},
        {"shape": ["None", "2"], "item_type": {"type": "integer"}, "type": "ndarray"},
        {"item_type": {"properties": {"a": {"item_type": {"type": "integer"}, "type": "list"}}, "type": "dict"}, "type": "list"}
    ]
    inputs = [
        1,
        1.23,
        False,
        [1, 2, 3],
        (1, 2, "hello"),
        {"a": 1, "b": 2, "c": 3},
        array([[1, 2], [3, 4]]),
        [{"a": [1, 2, 3, 4]}]
    ]
    for given, expected in zip(inputs, metadata):
        validate(given, expected)


if __name__ == "__main__":
    _test()
