from inspect import Signature
from pytest import raises
from numpy import ndarray
from typing import Hashable, List, Dict, Tuple, Any

from dlhub_sdk.utils import inspect
from dlhub_sdk.utils.types import compose_argument_block


class FakeType:
    __origin__ = True
    __args__ = (True,)


def _no_params_no_return():
    pass


def _bad_param(x) -> int:
    return 7


def _one_param(x: ndarray) -> ndarray:
    return x


def _multiple_params(a: float, b: float) -> float:
    return a + b


def _return_none(x: int) -> None:
    return


def _missing_ele_type(x: list) -> list:
    return x


def test_signature_to_input() -> None:
    assert inspect.signature_to_input(Signature.from_callable(_no_params_no_return)) == {"data_type": "python object",
                                                                                         "description": "", "python_type": "builtins.NoneType"}

    ndarray_metadata = compose_argument_block("ndarray", "", shape="Any")
    del ndarray_metadata["type"]
    assert inspect.signature_to_input(Signature.from_callable(_one_param)) == {"data_type": "ndarray", **ndarray_metadata}

    assert inspect.signature_to_input(Signature.from_callable(_multiple_params)) == {"data_type": "tuple", "description": "",
                                                                                     "element_types": [compose_argument_block("float", ""),
                                                                                                       compose_argument_block("float", "")]}

    with raises(TypeError):
        inspect.signature_to_input(Signature.from_callable(_bad_param))

    with raises(TypeError):
        inspect.signature_to_input(Signature.from_callable(_missing_ele_type))


def test_signature_to_output() -> None:
    assert inspect.signature_to_output(Signature.from_callable(_return_none)) == {"data_type": "python object", "description": "",
                                                                                  "python_type": "builtins.NoneType"}

    with raises(TypeError):
        inspect.signature_to_output(Signature.from_callable(_no_params_no_return))

    with raises(TypeError):
        inspect.signature_to_output(Signature.from_callable(_missing_ele_type))


def test_type_hint_to_metadata() -> None:
    assert inspect.type_hint_to_metadata(List[int]) == {"description": "", "item_type": {"description": "", "type": "integer"}, "type": "list"}

    assert inspect.type_hint_to_metadata(Tuple[int, float]) == {"description": "", "element_types": [{"description": "", "type": "integer"},
                                                                                                     {"description": "", "type": "float"}],
                                                                                   "type": "tuple"}

    assert inspect.type_hint_to_metadata(Dict[str, int]) == {"description": "", "properties": {}, "type": "dict"}

    assert inspect.type_hint_to_metadata(ndarray) == {"description": "", "shape": "Any", "type": "ndarray"}

    assert inspect.type_hint_to_metadata(None) == {"description": "", "type": "python object", "python_type": "builtins.NoneType"}

    assert inspect.type_hint_to_metadata(Any) == {"description": "", "type": "python object", "python_type": "typing.Any"}

    with raises(TypeError):
        inspect.type_hint_to_metadata(FakeType)


def test_name() -> None:
    assert inspect.name(int) == "int"
    assert inspect.name(tuple) == "tuple"
    assert inspect.name(Hashable) == "Hashable"
