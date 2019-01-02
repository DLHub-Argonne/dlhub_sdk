Argument Types
==============

DLHub supports many types of data as inputs and outputs to servables.
In this part of the guide, we describe what these types are and how to define them when describing an interface.
A full listing of the types is maintained in the `DLHub schemas repository <https://github.com/DLHub-Argonne/dlhub_schemas/blob/master/schemas/servable/argument_type.json>`_.
A utility for creating type definitions can also be found in the `DLHub SDK <source/dlhub_sdk.utils.html#module-dlhub_sdk.utils.types>`_.

float, integer, number, complex
-----------------------------------------------

There are a variety of ways to express numerical values in DLHub interfaces:
- ``number`` implies any real numerical value and implies there is limitation of the data being a float or integer.
- ``float`` and ``integer`` are available if it is necessary to ensure the values are stored as floats or integers.
- The ``complex`` argument type is used for complex numbers

string
------

Used for any string values.

boolean
-------

Used for Boolean values.

timedelta, datetime
-------------------

These data types define values associated with time.
``timedelta`` and ``datetime`` represent a length of time and a specific time, respectively.

python object
-------------

The ``python object`` type is used for data that cannot be expressed by other types.
The only required argument for the ``python object`` is the Python type of the
object by listed the Python class as ``python_type`` keyword.
For example, a Pandas Dataframe would be expressed as:

.. code-block:: json

    {
        "type": "python object",
        "python_type": "pandas.DataFrame"
    }

ndarray
-------

``ndarray`` values are matrices.
It is required to specify the shape using the ``shape`` keyword, which takes a list of integers are ``None`` values.
The ``null`` values in a shape definition represent that the dimension can take on any size.
The type of each value in the array can be defined using the ``item_type`` keyword, which takes a type definition as its only argument.
For example, an ``Nx3`` array of integers can be represented by:

.. code-block:: json

   {
      "type": "ndarray",
      "item_type": {"type": "integer"},
      "shape": [null, 3]
   }

list
----

List types define an ordered collection of indefinite length of all the same type of items.
Only the item type need be defined using the ``item_type`` keyword, which requires an argument type as its value.
For example, a list of 1D ``ndarray`` would be:

.. code-block:: json

    {
        "type": "list",
        "item_type": {
            "type": "ndarray",
            "shape": [null]
        }
    }

tuple
-----

Tuple types define an ordered collection of known length where each member can be a different type.
The item type of each member and, thereby, the length must be defined using the ``member_types`` keyword.
A tuple of a integer, float, and list of strings would be:

.. code-block:: json

    {
        "type": "tuple",
        "element_types": [
            {"type": "integer"},
            {"type": "float"},
            {"type": "list", "item_type": "string"}
        ]
    }

dict
----

The ``dict`` argument type is used for dictionary objects.
The data type requires the names and types of each key to be defined in the ``properties`` keyword.
For example, a dictionary with key "x" mapped to an integer and "y" mapped to a float would be:

.. code-block:: json

    {
        "type": "dict",
        "properties": {
            "x": {"type": "integer"},
            "y": {"type": "float"}
        }
    }
