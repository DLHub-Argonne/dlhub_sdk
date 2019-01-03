Servable Types
==============

DLHub can serve many different kinds of functions and machine learning models.
Each type of servable has a different tool (a "Model Class") that will aid you
in collecting the data needed to run the servable.
Here, we detail the types of servables available in DLHub and how to describe them.

Python Functions
----------------

It is possible to publish any Python function as a servable in DLHub.
DLHub currently supports two types of Python functions: static functions and class methods.
Static functions call members of Python modules and class methods involve calling
a function of a specific Python object.
Using ``numpy`` as an example, ``numpy.sum(x)`` involves calling a *static function* of the ``numpy`` module and
``x.sum()`` calls the ``sum`` *class method* of the ``ndarray`` ``x``.


Python Static Functions
+++++++++++++++++++++++

**Model Class**: `PythonStaticMethodModel <source/dlhub_sdk.models.servables.html#dlhub_sdk.models.servables.python.PythonStaticMethodModel>`_

Serving a Python function requires specifying the name of the module defining the function, the name of the function,
and the inputs/outputs of the function.
As an example, documenting the ``max`` function from ``numpy`` would start with::

    model = PythonStaticMethodModel.create_model('numpy', 'max', autobatch=False,
                                                         function_kwargs={'axis': 0})

The first arguments define the module and function name, and are followed by how the command is executed.
``autobatch=True`` would tell DLHub to run the function on each member of a list.
``function_kwargs`` defines the default keyword arguments for the function (in our case, ``axis=0``)

The next step is to define the arguments to the function::

    model.set_inputs('ndarray', 'Matrix', shape=[None, None])
    model.set_outputs('ndarray', 'Max of a certain axis', shape=[None])

Each of these functions takes the type of input and a short description for that input.
Certain types of inputs require further information (e.g., ndarrays require the shape of the array).
See `Argument Types <argument-types.html>`_ for a complete listing of argument types.

Using Static Functions to Create Special Interfaces
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Some servables required a specialized interface to make the software servable via DLHub.
For example, some preprocessing of the input may need to occur before execution.

For these cases, we define a static function in file named ``app.py`` and
create a Python servable for that interface function.

See our interface to ``SchNet`` as an example: `link <https://github.com/DLHub-Argonne/dlhub_containers/tree/master/schnet>`_.

Python Class Method
+++++++++++++++++++

**Model Class**: `PythonClassMethodModel <source/dlhub_sdk.models.servables.html#dlhub_sdk.models.servables.python.PythonClassMethodModel>`_

Python class methods are functions associated with a specific Python object.
DLHub needs both the file containing the object itself and documentation for the function.
As an example, consider a Python object using the following code::

    class ExampleClass:
        def __init__(self, a):
            self.a = a
        def f(self, x, b=1):
            return self.a * x + b
    x = ExampleClass(1)
    with open('pickle.pkl', 'wb') as fp:
        pkl.dump(x, fp)

The code to serve function ``f`` would be::

    model = PythonClassMethodModel.create_model('pickle.pkl', 'f')
    model.set_inputs('float', 'Input value')
    model.set_outputs('float', 'Output value')

This code defines the file containing the serialized object (``pickle.pkl``),
the name of the function to be run, and the types of the inputs and outputs.
Note that the syntax for defining inputs and outputs is the same as the static functions.

For this example, it is necessary to include a module defining ``ExampleClass`` in the required libraries::

    model.add_requirement('fake_module_with_exampleclass_on_pypi')

or adding the code that defines the class to a seperate file (e.g., ``example.py``) and adding that to the list
of files required by DLHub::

    model.add_file('example.py')

