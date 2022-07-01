from pytest import raises
from numpy import array

from dlhub_sdk.utils.validation import validate


def test_validation() -> None:
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


def test_validation_errs() -> None:
    with raises(TypeError):
        validate("1", {"type": "integer"})
    with raises(ValueError):
        validate(array([1, 2]), {"shape": ["1"], "type": "ndarray"})
