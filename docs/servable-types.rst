Servable Types
==============

DLHub supports many different types of machine learning models and functions.
This part of the guide documents how to describe each of these types of servables for publication in DLHub.

Python Functions
----------------

While there are specialized routes for publishing different types of deep learning models, it is possible to publish
any Python function as a servable in DLHub.
We break Python functions into two distinct classifications that each have different metadata requirements:
static functions and class methods.
Static functions involve calling functions that are members of Python modules and class methods involve calling
a function of a specific Python object.
Using ``numpy`` as an example, ``numpy.sum(x)`` involves calling a static method of the ``numpy`` module and
``x.sum()`` calls the ``sum`` method of the ``ndarray`` ``x``.


Python Static Functions
+++++++++++++++++++++++

**Model Class**: `PythonStaticMethodModel <source/dlhub_sdk.models.servables.html#dlhub_sdk.models.servables.python.PythonStaticMethodModel>`_

Serving a Python function requires specifying the name of the module defining the function, the name of the function,
and the inputs/outputs of the function.
As an example, documenting the ``max`` function from ``numpy`` would start with::

    model = PythonStaticMethodModel.create_model('numpy', 'max', autobatch=False,
                                                         function_kwargs={'axis': 0})

The first two arguments define the module and function name, and are followed by further documentation for how the command is executed.
``autobatch=True`` is a special feature of DLHub that automatically runs the function on each member of a list, which
we do not use in this example.
``function_kwargs`` defines the default keyword arguments for the function.
Here, we define the ``axis`` keyword argument to have a default value of ``0``.
Note that DLHub will allow this default value to be overridden when running the function later.

The next step is to define the arguments to the function::

    model.set_inputs('ndarray', 'Matrix', shape=[None, None])
    model.set_outputs('ndarray', 'Max of a certain axis', shape=[None])

Each of these functions takes the type of input and a short description for that input.
Certain types of inputs require further information (e.g., ndarrays require the shape of the array).
See `Argument Types <argument-types.html>`_ for a complete listing of argument types.

Using Static Functions to Create Special Interfaces
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We commonly find that some servables required a specialized interface to make the software servable via DLHub.
There may be some preprocessing of the input before it is sent to a function or the Tensorflow environment
needs to be reset before invoking the model.

For these cases, we have adopted a pattern of defining this interface as a special function in file named ``app.py`` and
creating a Python static method servable for that function.

See our interface to ``SchNet`` as an example: `link <https://github.com/DLHub-Argonne/dlhub_containers/tree/master/schnet>`_.

Python Class Method
+++++++++++++++++++

**Model Class**: `PythonClassMethodModel <source/dlhub_sdk.models.servables.html#dlhub_sdk.models.servables.python.PythonClassMethodModel>`_

Python class methods are functions associated with a specific Python object.
To serve these types of methods, DLHub needs both the file containing the object itself and the information about the function.
As an example, consider we create a Python object using the following code::

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

We define the file containing the serialized object (``pickle.pkl``), the name of the function to be run, and
the types of the inputs and outputs.
The syntax for defining the inputs and outputs is the same as the static functions.

For this example, we would need to include a module defining ``ExampleClass`` in the required libraries::

    model.add_requirement('fake_module_with_exampleclass_on_pypi')

or adding the code that defines the class to a seperate file (e.g., ``example.py``) and adding that to the list
of files required by DLHub::

    model.add_file('example.py')
