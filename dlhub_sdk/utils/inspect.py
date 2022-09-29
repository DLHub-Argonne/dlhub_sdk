from inspect import Signature
from typing import Any, Dict, List, Tuple, Union
from numpy import ndarray

from dlhub_sdk.utils.types import compose_argument_block, PY_TYPENAME_TO_JSON


def signature_to_input(sig: Signature) -> Dict[str, Any]:
    """Use a function signature to generate the input to model.set_inputs()"""
    if len(sig.parameters.values()) == 0:
        return {"data_type": "python object", "description": "", "python_type": "builtins.NoneType"}  # mirros last clause of type_hint_to_metadata

    metadata = []
    for param in sig.parameters.values():
        # if the parameter is not type hinted, auto-extraction cannot proceed
        if param.annotation is param.empty:
            raise TypeError(f"Please provide a type hint for the parameter: {param.name}")
        # if the parameter is an iterable and its element type(s) were not provided, auto-extraction cannot proceed
        # this condition is sufficient because a proper type hint of such a type will not be the type itself
        elif param.annotation in {list, tuple}:  # dict could be included, but those values are unused in type_hint_to_metadata as of now
            raise TypeError(f"Please provide the type(s) that the parameter: {param.name} is expected to accept")

        metadata.append(type_hint_to_metadata(param.annotation))

    if len(metadata) == 1:
        metadata = metadata[0]  # get the item from the single item list
        return {"data_type": metadata.pop("type"), **metadata}  # change the name of the "type" property and merge the rest in

    return {"data_type": "tuple", "description": "", "element_types": metadata}


def signature_to_output(sig: Signature) -> Dict[str, Any]:
    """Use a function signature to generate the input to model.set_outputs()"""
    # if the return value is not type hinted, auto-extraction cannot proceed
    if sig.return_annotation is sig.empty:
        raise TypeError("Please provide a type hint for the return type of your function")
    if sig.return_annotation in {list, tuple}:  # dict could be included, but those values are unused in type_hint_to_metadata as of now
        raise TypeError("Please provide the type(s) of elements in the return type hint")

    metadata = type_hint_to_metadata(sig.return_annotation)

    return {"data_type": metadata.pop("type"), **metadata}  # change the name of the "type" property and merge the rest in


def type_hint_to_metadata(hint: Union[Tuple, List, Dict, type]) -> Dict[str, str]:
    """Take a type hint and convert it into valid DLHub metadata
    Args:
        hint (type hint | type): a type hint can be either a type (e.g. int) or a GenericAlias/typing type (e.g. list[int]/List[int]),
                                 these objects are retrieved from Signature object properties
    Returns:
        (dict): the metadata for the given hint
    """
    if hasattr(hint, "__origin__") and hasattr(hint, "__args__") and len(hint.__args__) > 0:  # differentiates subscripted type hint objects
        # in a type hint, the __origin__ is the outer type (e.g. list in list[int])
        # and the inner type, int, would be at __args__[0]
        if hint.__origin__ is list:
            return compose_argument_block("list", "", item_type=type_hint_to_metadata(hint.__args__[0]))  # __args__ is a tuple even if it's length=1
        if hint.__origin__ is tuple:
            return compose_argument_block("tuple", "", element_types=[type_hint_to_metadata(x) for x in hint.__args__])
        if hint.__origin__ is dict:
            return compose_argument_block("dict", "", properties={})  # without the keys no part of the hint can be properly processed

        raise TypeError("Fatal error: unknown paramaterized type encountered")
    else:
        if hint is ndarray:
            return compose_argument_block("ndarray", "", shape="Any")

        json_name = PY_TYPENAME_TO_JSON.get(hint)
        if json_name:
            return compose_argument_block(json_name, "")

        if hint is None:
            hint = type(None)
        return compose_argument_block("python object", "", python_type=f"{hint.__module__}.{name(hint)}")


def name(t: type) -> str:
    """Return the name of type t
       (typing types do not have the normal __qualname__ attribute in some Python versions, in those versions they have a _name instead)
    Args:
        t (type): the type which needs to be identified
    Returns:
        (string): the name of type t
    """
    if hasattr(t, "__qualname__"):
        return t.__qualname__

    return t._name
