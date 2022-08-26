from io import IOBase
from pathlib import Path
from typing import Hashable, List, Tuple, Union, Any
from numpy import ndarray, void
from datetime import datetime, timedelta
import warnings

from dlhub_sdk.utils.types import simplify_numpy_dtype


class ValidationWarning(RuntimeWarning):
    """Brought to the user's attention when a validation step has dubious accuracy"""


def _type_name_to_type(name: str) -> Union[type, Tuple[type]]:
    """Convert string type name to Python type object

    Args:
        name (string): The name of the type in question
    Returns:
        type: the type object whose __name__ is name (or None in the case of "None")
    Raises:
        ValueError: If name is not matched to a type object
    """
    type_table = {"boolean": bool,
                  "integer": int,
                  "float": (int, float),
                  "number": (int, float, complex),
                  "string": str,
                  "file": (IOBase, Path, str),
                  "ndarray": ndarray,
                  "datetime": datetime,
                  "timedelta": timedelta}

    # lookup the type name in the conversion table and the builtin names
    try:
        return type_table.get(name) or __builtins__[name]  # getattr(__builtins__, name) if __builtins__ is a module
    except KeyError:  # AttributeError if __builtins__ is a module
        raise ValueError(f"found an unknown type name in servable metadata: {name}") from None


def _generate_err(err_type: Exception, path: List[Tuple[str, Hashable]], expected: type = None, given: type = None, *, msg: str = None) -> Exception:
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

    # None does not have a __name__ attribute
    if expected is not None:
        expected = expected.__name__
    if given is not None:
        given = given.__name__

    loc = " at input" if path else ""  # loc should start with ' at input' if an index will be supplied, or nothing if not

    # build the expected and loc parts of the error message using the data stored in path
    for jump in reversed(path):
        expected = f"{jump[0]}[{expected}]"
    for jump in path:
        loc += f"[{repr(jump[1])}]"

    if msg:
        return err_type(msg.format(loc=loc))  # allows callers to use "{loc}" in their msg to access the variable with that name in this scope
    return err_type(f"dl.run given improper input type: expected {expected}, received {given}{loc}")


def validate(inputs: Any, db_entry: dict, path: List[Tuple[str, Hashable]] = None) -> None:
    """Perform the complete validation step

    Args:
        inputs (Any): The input that will be provided to a servable
        db_entry (dict): The metadata that inputs is validated against
        path (list): List that stores the path through the data to the current point (items in the form [dtype: str, index/key: Hashable])
    Returns:
        None
    Raises:
        ValueError: If any value in inputs does not match the db_entry
        TypeError: If any type in inputs does not match the db_entry
    """
    path = [] if path is None else path  # handles default argument (path=None)

    expected_input_type = _type_name_to_type(db_entry["type"])  # get the dtype that the metadata expects for inputs
    _validate_type(inputs, expected_input_type, path)  # check inputs against that type

    # if inputs is iterable, then also check each of its elements against the metadata
    if expected_input_type is list:
        _validate_list(inputs, db_entry, path)

    elif expected_input_type is tuple:
        _validate_tuple(inputs, db_entry["element_types"], path)

    elif expected_input_type is ndarray:
        _validate_ndarray(inputs, db_entry["shape"], db_entry, path)

    elif expected_input_type is dict:
        _validate_dict(inputs, db_entry["properties"], path)
    # it is intentional that nothing is done in the absence of an Exception


def _validate_type(obj: Any, in_type: type, path: List[Tuple[str, Hashable]], *, class_: bool = False) -> None:
    """Compare the type of obj with in_type

    Args:
        obj (Any): The object whose type needs to be validated
        in_type (type): The type that obj is expected to have
        path (list): List that stores the path through the data to the current point (items in the form [dtype: str, index/key: Hashable])
        class_ (boolean): Whether to consider obj as an instance or a class
    Returns:
        None
    Raises:
        TypeError: If the types do not match
    """
    check_func = issubclass if class_ else isinstance  # the relationship between obj and in_type depends on class_

    # find the type of obj, if obj is a class its type is obj rather than 'type'
    if obj is None:  # avoids dealing with 'NoneType'
        obj_type = None
    elif class_:
        obj_type = obj
    else:
        obj_type = type(obj)

    if not check_func(obj, in_type):
        raise _generate_err(TypeError, path, in_type, obj_type)
    if check_func(obj, bool) and in_type is int:
        # warning message is delivered when a boolean is (perhaps) incorrectly considered an integer
        warnings.warn("Boolean input has been validated as type Integer, this is likely unintended.", ValidationWarning, stacklevel=2)


def _validate_list(li: list, db_entry: dict, path: List[Tuple[str, Hashable]]) -> None:
    """Recursively validate each of the elements in li against db_entry["item_type"]

    Args:
        li (list): The list whose items need to have their type validated
        db_entry (dict): The entry that stores type data for li
        path (list): List that stores the path through the data to the current point (items in the form [dtype: str, index/key: Hashable])
    Returns:
        None
    Raises:
        TypeError: If any of the items' types do not match
    """
    path.append(["list", None])  # add the current dtype and index to the path
    for i, item in enumerate(li):
        path[-1][1] = i  # update the index that would be shown in an error message
        validate(item, db_entry["item_type"], path)
    path.pop()  # since checking for this object has concluded, remove it from the path


def _validate_tuple(tup: tuple, db_entries: List[dict], path: List[Tuple[str, Hashable]]) -> None:
    """Recursively validate each of the elements in tup against the corresponding entry in db_entries

    Args:
        tup (tuple): The tuple whose items need to have their type validated
        db_entries (list): The list of dicts that store the metadata for each item in tup
        path (list): List that stores the path through the data to the current point (items in the form [dtype: str, index/key: Hashable])
    Returns:
        None
    Raises:
        ValueError: If the number of entries and tuple elements do not match
        TypeError: If any of the items' types do not match
    """

    # if the number of elements in tup differs from the number of parameters set by the metadata, an error can be raised immediately
    if len(tup) != len(db_entries):
        raise _generate_err(ValueError, path, msg=f"dl.run expected tuple of length {len(db_entries)}, recieved tuple with length {len(tup)}"
                                                  + "{loc}")

    path.append(["tuple", None])
    for i, (given, expected) in enumerate(zip(tup, db_entries)):
        path[-1][1] = i
        validate(given, expected, path)
    path.pop()


def _validate_ndarray(arr: ndarray, shape: List[str], db_entry: dict, path: List[Tuple[str, Hashable]]) -> None:
    """Compare the shape of arr with shape and recursively validate each of the elements in arr against db_entry["item_type"]

    Args:
        arr (ndarray): The ndarray whose shape and items need to be validated
        shape (list): The shape that arr is expected to have
        db_entry (dict): The entry where type data may or may not be retrieved
        path (list): List that stores the path through the data to the current point (items in the form [dtype: str, index/key: Hashable])
    Returns:
        None
    Raises:
        ValueError: If arr.shape does not match shape
        TypeError: If any of the items' types do not match
    """
    shape = tuple(int(x) if x != "None" else x for x in shape)  # convert the string metadata into integers, if applicable

    # store an error to make code more readable
    shape_err = _generate_err(ValueError, path, msg=f"dl.run given improper input: expected ndarray.shape = {shape}, received shape: {arr.shape}"
                                                    + "{loc}")

    # if the shape of the array does not match the metadata, an error can be raised immediately
    if len(arr.shape) != len(shape):
        raise shape_err
    if not all(map(lambda t: t[0] == t[1] or t[1] == "None", zip(arr.shape, shape))):
        raise shape_err

    # it is not required for there to be an "item_type" field, but it should be checked if present
    entry = db_entry.get("item_type")
    if entry and len(arr) > 0:
        arr_type_str = simplify_numpy_dtype(arr.dtype)

        # this logic handles cases where arr.item(0) would return a dubious object
        if arr_type_str == "python object" and arr.dtype is not void:
            validate(arr.item(0), entry, path)
        else:
            _validate_type(_type_name_to_type(arr_type_str), _type_name_to_type(entry["type"]), path, class_=True)


def _validate_dict(dct: dict, props: dict, path: List[Tuple[str, Hashable]]) -> None:
    """Recursively validate each of the pairs in dct against props

    Args:
        dct (dict): The dict whose keys and values need to be validated
        props (dict): The dict that describes the expected keys and values
        path (list): List that stores the path through the data to the current point (items in the form [dtype: str, index/key: Hashable])
    Returns:
        None
    Raises:
        ValueError: If dct is missing a key from props or a value in dct causes an error
        TypeError: If any of the values' types do not match
    """

    # props can be an empty dict, if that is the case: ignore any checks
    if props:
        path.append(["dict", None])
        # make sure that no keys are used that the metadata does not anticipate
        for key in dct:
            path[-1][1] = key
            if key not in props:
                raise _generate_err(ValueError, path, msg=f"dl.run given improper input: given unexpected dictionary key: {repr(key)}"+"{loc}")
        # ensure that all keys the metadata expects are present, and if they are: recursively validate their data
        for key in props:
            path[-1][1] = key
            if key not in dct:
                raise _generate_err(ValueError, path, msg=f"dl.run given improper input: expected dictionary key: {repr(key)} to be present"+"{loc}")
            validate(dct[key], props[key], path)
        path.pop()
