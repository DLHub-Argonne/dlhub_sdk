from pytest import raises
from numpy import array

from dlhub_sdk.utils.validation import validate


def test_validation() -> None:
    metadata = [
        {"type": "integer"},
        {"type": "integer"},
        {"type": "float"},
        {"type": "boolean"},
        {"item_type": {"type": "integer"}, "type": "list"},
        {"element_types": [{"type": "integer"}, {"type": "integer"}, {"type": "string"}], "type": "tuple"},
        {"properties": {"a": {"type": "integer"}, "b": {"type": "integer"}, "c": {"type": "integer"}}, "type": "dict"},
        {"shape": "Any", "type": "ndarray"},
        {"shape": "Any", "type": "ndarray"},
        {"shape": ["None", "2"], "item_type": {"type": "integer"}, "type": "ndarray"},
        {"shape": ["1"], "item_type": {"properties": {"a": {"type": "integer"}}, "type": "dict"}, "type": "ndarray"},
        {"item_type": {"properties": {"a": {"item_type": {"type": "integer"}, "type": "list"}}, "type": "dict"}, "type": "list"}
    ]
    inputs = [
        1,
        True,
        1.23,
        False,
        [1, 2, 3],
        (1, 2, "hello"),
        {"a": 1, "b": 2, "c": 3},
        array([1, 2, 3]),
        array([[1], [2]]),
        array([[1, 2], [3, 4]]),
        array([{"a": 1}]),
        [{"a": [1, 2, 3, 4]}]
    ]

    for given, expected in zip(inputs, metadata):
        validate(given, expected)


def test_validation_errs() -> None:
    with raises(ValueError):
        validate(1, {"type": "nonsense"})

    with raises(TypeError):
        validate(None, {"type": "integer"})

    with raises(TypeError):
        validate({"a": [1, 2, 3, 4.]}, {"properties": {"a": {"item_type": {"type": "integer"}, "type": "list"}}, "type": "dict"})

    with raises(ValueError):
        validate((1, 2, "hello"), {"element_types": [{"type": "integer"}, {"type": "integer"}], "type": "tuple"})

    with raises(ValueError):
        validate(array([[1, 2], [3, 4]]), {"shape": ["None"], "type": "ndarray"})

    with raises(ValueError):
        validate(array([1, 2]), {"shape": ["1"], "type": "ndarray"})

    with raises(ValueError):
        validate({"a": 1, "b": 2, "c": 3}, {"properties": {"a": {"type": "integer"}, "b": {"type": "integer"}}, "type": "dict"})

    with raises(ValueError):
        validate({"a": 1, "b": 2}, {"properties": {"a": {"type": "integer"}, "b": {"type": "integer"}, "c": {"type": "integer"}}, "type": "dict"})
