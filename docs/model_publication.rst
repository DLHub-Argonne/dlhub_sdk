Model Publication Guide
=======================

Publishing a new model to DLHub requires to main steps: describing the model and submitting it.
In this guide, we provide a tutorial for describing different kinds of models and an overview of the routes available for publishing the descriptions to DLHub.

Model Description Philosophy
----------------------------

The goal of model description is to provide the information needed for both humans and computers to use the model.
The format how to how describe these models are `available in full on GitHub <https://github.com/DLHub-Argonne/dlhub_schemas>`_,
but understanding the full JSON schema is not required for publishing a model to DLHub.
To start, we will briefly describe what metadata (e.g., information describe the model) is being stored and why we request it.

We use the `DataCite <https://datacite.org/>`_ schema for describing each model to humans.
DataCite requires metadata that may be very familiar to the academic community: a title, author list, affiliations, references, etc.
Titles, author lists, and names are the only required fields but we highly recommend writing and abstract and providing references.
Make sure to answer questions like "what does this model take as input and what does it generate?" and "what was the model trained on?".
Success for writing a robust description means that your model is more likely to be used and you receive fewer emails asking about what the model does or how to use it.

Our approach for describing a model requires capturing what computational environment is needed (e.g., which libraries),
what files are needed to load the model, and a definition of the input and output functions.
We follow a similar approach to `repo2docker <https://repo2docker.readthedocs.io/en/latest/>`_ for describing the computational environment.
``repo2docker`` functions by describing the environment in a collection of `configuration files <https://repo2docker.readthedocs.io/en/latest/config_files.html>`_,
which include information such as the Python libraries to be installed or a Dockerfile describing the complete environment.
The SDK also provides additional utilities for specifying Python libraries to simplify describing models that only require pip-installable Python libraries.

Describing how to run a model varies significantly on the type.
For a basic example, consider Python functions.
If the function is a static function, DLHub needs to know the module and name of the function.
If the function is a class method, DLHub needs the pickle file containing the object and the name of the function.
In both cases, the type of the input (e.g., string, integer, matrix) are required to know what kinds of tools can be combined
with the model and for human users to know how to use them.
As described in the following section, we provide tools for common types of models to automatically identify information
about how to run the model or to guide you on describing how to employ the model.

Preparing a Model for Publication
---------------------------------

The procedure for submitting a model to DLHub contains three steps: describing what the
model does, describing how to run it, and submitting it to the service.
The DLHub SDK contains utilities for simplifying each step of this process.

Step 1: Preparing the Submission Directory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You will first need to install the `dlhub_cli <https://github.com/DLHub-Argonne/dlhub_cli>`_
and `dlhub_sdk <https://github.com/DLHub-Argonne/dlhub_sdk>`_ on your system.
Both libraries are on PyPi, so you can install them with::

    $ pip install dlhub_sdk dlhub_cli

The first step in the model submission process is to autheticate with dlhub: :code:`dlhub login`

Next, call :code:`dlhub init` in the directory to generate a template for describing the model.
The template is a Python script named `describe_model.py`, which contains instructions for how to provide the metadata
for your model.

Step 2: Describing a Model
~~~~~~~~~~~~~~~~~~~~~~~~~~

The template file created in Step 1 provides a framework for describing how to use your machine learning model.
The provenance information (e.g., "who made this model?", "why?") is the same for all types of models.
Where the description part differs is in how to specify how to run the models.

DLHub currently supports several different deep learning frameworks and other types of servable models:

- Tensorflow
- Keras
- Scikit-Learn
- Generic Python Functions

Follow the instructions for describing each of these model types.
Once finished, the ``dlhub.json`` file created by your model will have all the information needed by DLHub to run your model

Step 3: Submitting the Model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

TBD: Currently overhauling the model submission process
