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

Functions that take more than one argument (e.g., ``f(x, y)``) require you to tell DLHub
to unpack the inputs before running the function.
As an example::

    from dlhub_sdk.utils.types import compose_argument_block
    model = PythonStaticMethodServable.from_function_pointer(f)
    model.set_inputs('tuple', 'Two numbers', element_types=[
        compose_argument_block('float', 'A number'),
        compose_argument_block('float', 'A second number')
    ])
    model.set_unpack_inputs(True)

Note that we used an input type of "tuple" to indicate that the function takes a fixed number of arguments.
You can also use a type of "list" for functions that take a variable number of inputs.

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

As with the Python static methods, you can specify the functions with multiple arguments using ``set_unpack_inputs``.

Keras Models
------------

**Model Class**: `KerasModel <source/dlhub_sdk.models.servables.html#dlhub_sdk.models.servables.keras.KerasModel>`_

DLHub serves Keras models using the HDF5 file saved using the ``Model.save`` function
(see `Keras FAQs <https://keras.io/getting-started/faq/#savingloading-whole-models-architecture-weights-optimizer-state>`_).
The methods described here also work with ``tf.keras`` though you should use the `Tensorflow <#tensorflow-graphs>`_
loader if you saved the model into Tensorflow's ``SavedModel`` format.
As an example, the description for a Keras model created using:

.. code-block:: python

    model = Sequential()
    model.add(Dense(16, input_shape=(1,), activation='relu', name='hidden'))
    model.add(Dense(1, name='output'))
    model.compile(optimizer='rmsprop', loss='mse')
    model.fit(X, y)
    model.save('model.h5')

can be generated from only the h5 model:

.. code-block:: python

    model_info = KerasModel.create_model('model.h5')

Models with weights and architecture as separate files can be described using:

.. code-block:: python

	model_info = KerasModel.create_model('model.h5', arch_path='arch.json')

Keras also allows users to add their own custom layers to their models for any custom operation
that has trainable weights. Use this when the Keras Lambda layer does not apply. In Keras, 
these layers can be added when loading the model:

.. code-block:: python

	model = load_model('model.h5', custom_objects={'CustomLayer': CustomLayer})

Adding custom layers to a DLHub description can be achived with the ``add_custom_object`` method, which takes the name
and class of the custom layer:

.. code-block:: python

	model_info.add_custom_object('CustomLayer', CustomLayer)

See more info on creating custom Keras layers `here <https://keras.io/layers/writing-your-own-keras-layers/>`_.

The DLHub SDK reads the architecture in the HDF5 file and determines the inputs
and outputs automatically:

.. code-block:: json

    {
      "methods": {
        "run": {
          "input": {
            "type": "ndarray", "description": "Tensor", "shape": [null, 1]
          },
          "output": {
            "type": "ndarray", "description": "Tensor", "shape": [null, 1]
          },
          "parameters": {},
          "method_details": {
            "method_name": "predict"
          }
        }
      }
    }

We recommended changing the descriptions for the inputs and outputs from their
default values::

    model_info['servable']['methods']['run']['output']['description'] = 'Response'

but the model is ready to be served without any modifications.

The SDK also determines the version of Keras on your system, and saves that in the requirements.

PyTorch Models
--------------

**Model Class**: `TorchModel <source/dlhub_sdk.models.servables.html#dlhub_sdk.models.servables.pytorch.TorchModel>`_

DLHub serves PyTorch models using the .pt file saved using the ``torch.save`` function
(see `PyTorch FAQs <https://pytorch.org/tutorials/beginner/saving_loading_models.html>`_).
As an example, the description for a PyTorch model created using:

.. code-block:: python

    class Net(nn.Module):
      def __init__(self):
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(1, 20, 5, 1)
        self.conv2 = nn.Conv2d(20, 50, 5, 1)
        self.fc1 = nn.Linear(4*4*50, 500)
        self.fc2 = nn.Linear(500, 10)

      def forward(self, x):
        x = F.relu(self.conv1(x))
        x = F.max_pool2d(x, 2, 2)
        x = F.relu(self.conv2(x))
        x = F.max_pool2d(x, 2, 2)
        x = x.view(-1, 4*4*50)
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        return F.log_softmax(x, dim=1)

    model = Net()
    torch.save(model, 'model.pt')

can be generated from the .pt file and the shapes of the input and output arrays.

.. code-block:: python

    model_info = TorchModel.create_model('model.pt', (None, 1, 28, 28), (None, 10))

DLHub will need the definition for the ``Net`` module in order to load and run it.
You must add the Python libraries containing the module definitions as requirements,
or add the files defining the modules to the servable definition.

.. code-block:: python

    model_info.add_file('Net.py')

As with Keras, we recommended changing the descriptions for the inputs and outputs from their
default values::

    model_info['servable']['methods']['run']['output']['description'] = 'Response'

but the model is ready to be served without any modifications.

In some cases, you may need to specify the data types of your input array(s) using the keyword arguments of ``create_model``.
The type specifications are needed because PyTorch does not do type casting automatically.
If in doubt, the data type is ``float`` and you can use the default settings.

The SDK also determines the version of Torch on your system, and saves that in the requirements.

TensorFlow Graphs
-----------------

**Model Class**: `TensorFlowModel <source/dlhub_sdk.models.servables.html#dlhub_sdk.models.servables.tensorflow.TensorFlowModel>`_

DLHub uses the same information as `TensorFlow Serving <https://www.tensorflow.org/serving/>`_ for
serving a TensorFlow model.

DLHub supports multiple functions to be defined for the same ``SavedModel``
servable, but requires one function is marked with ``DEFAULT_SERVING_SIGNATURE_DEF_KEY``.

The SDK also determines the version of TensorFlow installed on your system,
and lists it as a requirement.

How these models are created is very different between TF1 and TF2.

TF1
+++

Save your model using the ``SavedModelBuilder`` as described
in the `TensorFlow v1.0 <https://www.tensorflow.org/versions/r1.15/api_docs/python/tf/saved_model/Builder>`_.
As an example, consider a graph expressing :math:`y = x + 1`::


    # Create the graph
    with tf.Session() as sess:
        x = tf.placeholder('float', shape=(None, 3), name='Input')
        y = x + 1

        # Prepare to save the function
        builder = tf.saved_model.builder.SavedModelBuilder('./export')

        #  Make descriptions for the inputs and outputs
        x_desc = tf.saved_model.utils.build_tensor_info(x)
        y_desc = tf.saved_model.utils.build_tensor_info(y)

        # Create a function signature
        func_sig = tf.saved_model.signature_def_utils.build_signature_def(
            inputs={'x': x_desc},
            outputs={'y': y_desc},
            method_name='run'
        )

        # Add the session, graph, and function signature to the saved model
        builder.add_meta_graph_and_variables(
            sess, [tf.saved_model.tag_constants.SERVING],
            signature_def_map={
                tf.saved_model.signature_constants.DEFAULT_SERVING_SIGNATURE_DEF_KEY: func_sig
            }
        )

        # Write the files
        builder.save()

The DLHub SDK reads the ``./export`` directory written by this code::

    metadata = TensorFlowModel.create_model("./export")

to generate metadata describing which functions were saved:

.. code-block:: json

    {
      "methods": {
        "run": {
          "input": {
            "type": "ndarray", "description": "x", "shape": [null, 3]
          },
          "output": {
            "type": "ndarray", "description": "y", "shape": [null, 3]
          },
          "parameters": {},
          "method_details": {
            "input_nodes": ["Input:0"],
            "output_nodes": ["add:0"]
          }
        }
      }
    }


TF2
+++

Follow the instructions in `Tensorflow's documentation <https://www.tensorflow.org/guide/saved_model>`_
to save your model into the SavedModel format.
DLHub requires you to specify the signatures for each of your function you wish to
serve, which means you must either specify the input signature when defining the ``tf.function``
or create a concrete version of the function (see
`documentation <https://www.tensorflow.org/guide/saved_model#specifying_signatures_during_export>`_).

The following example shows how to save a ``tf.Module`` with one function without a signature
and a second with a signature.

.. code-block:: python

        class CustomModule(tf.Module):

        def __init__(self):
            super().__init__()
            self.m = tf.Variable([1.0, 1.0, 1.0], name='slope')

        @tf.function
        def __call__(self, x):
            y = self.m * x + 1
            return y

        @tf.function(input_signature=[tf.TensorSpec([], tf.float32),
                                      tf.TensorSpec((None, 3), tf.float32)])
        def scalar_multiply(self, z, x):
            return tf.multiply(z, x, name='scale_mult')

    module = CustomModule()

    # Make a concrete version of __call__
    call = module.__call__.get_concrete_function(tf.TensorSpec((None, 3)))

    tf.saved_model.save(
        module, tf_export_path, signatures={
            tf.saved_model.DEFAULT_SERVING_SIGNATURE_DEF_KEY: call,
            'scalar_multiply': module.scalar_multiply
        }
    )

The DLHub SDK will automatically recognize the function signatures and use them
to construct a servable accordingly::

    metadata = TensorFlowModel.create_model("./export")

will generate metadata describing which functions were saved:



.. code-block:: json

    {
      "run": {
        "input": {
          "type": "ndarray", "description": "x:0", "shape": [null, 3],
          "item_type": {"type": "float"}
        },
        "output": {
          "type": "ndarray", "description": "Identity:0", "shape": [null, 3],
          "item_type": {"type": "float"}
        },
      }, "scalar_multiply": {
        "input": {
          "type": "tuple", "description": "Several tensors",
          "element_types": [{
              "type": "ndarray", "description": "x:0", "shape": [null, 3], "item_type": {"type": "float"}
            }, {
              "type": "ndarray", "description": "z:0", "shape": [], "item_type": {"type": "float"}
            }
          ]
        },
        "output": {
          "type": "ndarray", "description": "Identity:0", "shape": [null, 3],
          "item_type": {"type": "float"}
        },
      }
    }

Scikit-Learn Models
-------------------

**Model Class**: `ScikitLearnModel <source/dlhub_sdk.models.servables.html#dlhub_sdk.models.servables.sklearn.ScikitLearnModel>`_

DLHub supports scikit-learn models saved using either pickle or joblib.
The saved models files do not always contain the number of input features
for the model, so they need to provided along with the serialization method
and, for classifiers, the class names::

    # Loading SVC trained on the iris dataset
    model_info = ScikitLearnModel.create_model('model.pkl', n_input_columns=4, classes=3)

Given this information, the SDK generates documentation for how to invoke the model:

.. code-block:: json

    {
      "methods": {
        "run": {
          "input": {
            "type": "ndarray",
            "shape": [null, 4],
            "description": "List of records to evaluate with model. Each record is a list of 4 variables.",
            "item_type": {"type": "float"}
          },
          "output": {
            "type": "ndarray",
            "shape": [null, 3],
            "description": "Probabilities for membership in each of 3 classes",
            "item_type": {"type": "float"}
          },
          "parameters": {},
          "method_details": {
            "method_name": "_predict_proba"
          }
        }
      }
    }

The SDK will automatically document the type of model and extract the scikit-learn
version used to save the model, which it includes in the requirements.
