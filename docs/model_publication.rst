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
The template is a Python script named ``describe_model.py``, which contains instructions for how to provide the metadata
for your model.

Step 2: Describing a Model
~~~~~~~~~~~~~~~~~~~~~~~~~~

The template file created in Step 1 provides a framework for describing how to use your machine learning model.
The provenance information (e.g., "who made this model?", "why?") and computational environment are the same for all types of models.
Where the description part differs is in how to specify how to run the models.

Describing the Computational Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There are two routes for specifying environment: defining Python libraries or using ``repo2docker``.

Basic Route: Specifying Python Libraries
++++++++++++++++++++++++++++++++++++++++

The computational environment for many models can be defined by only the required Python packages.
If this is true for your model, edit the ``describe_model.py`` file to include these requirements::

    # Add a specific requirement without version information
    model.add_requirement('library')

    # Autodetect the version installed on your environment
    model.add_requirement('library', 'detect')

    # Get the latest version on PyPI
    model.add_requirement('library', 'latest')

    # Get a specific version
    model.add_requirement('library', '1.0.0b')

Advanced: Using ``repo2docker``
+++++++++++++++++++++++++++++++

DLHub uses the configuration files specified by `repo2docker <https://repo2docker.readthedocs.io>`_ to define a complicated computational environment.
We refer you to the `documentation for repo2docker <https://repo2docker.readthedocs.io/en/latest/config_files.html>`_ to
learn how to create these configuration files.
Once you have created the files, edit the ``describe_model.py`` to point to the directory containing the files::

    # Include repo2docker files in current directory
    model.parse_repo2docker_configuration()

    # Include repo2docker files in a different directory
    model.parse_repo2docker_configuration('../another/path')

Describing the Model
^^^^^^^^^^^^^^^^^^^^

DLHub currently supports several different deep learning frameworks and other types of servable models:

- `Generic Python Functions <servable-type/python.html>`_
- Tensorflow
- Keras
- Scikit-Learn

Follow the instructions for describing each of these model types.
Once finished, the ``dlhub.json`` file created by your model will have all the information needed by DLHub to run your model

Step 3: Submitting the Model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are several routes for submitting a model to DLHub.

Recommended: Publishing Model to Git Repository
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Our recommended route for submitting models to DLHub is to first publish the model on a publicly-accessible git repository.
You will need to add the ``dlhub.json`` file to your git repository along with all files mentioned in that model description.
The weights for a model can occasionally be large enough to cause performance issues with git and, in those cases, we
recommend using `git-lfs <https://git-lfs.github.com/>`_ to publish those files.
For files that are surpass the limits of GitHub and ``git-lfs`` to handle (~GBs), consider `using Globus to submit the models <#send-data-via-globus>`_.

After publishing all associated file to GitHub, use the DLHub CLI to request DLHub imports a model from GitHub::

    # Publish from the root folder of a git repository
    $ dlhub publish --repository https://github.com/ryanchard/dlhub_publish_example

    # Publish from another path within of a git repository
    $ dlhub publish --repository https://github.com/ryanchard/dlhub_publish_example another/path

*Note: Publication from a non-root directory is still under development*

Publication via Direct Upload
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

*Note: This feature is under development*

It is also possible to submit models directly from your computer to DLHub via HTTP::

    $ dlhub publish --local

This route is recommend for models you do not want to share publicly and have small file sizes.

Send Data via Globus
^^^^^^^^^^^^^^^^^^^^

*Note: This feature is under development*

`Globus Transfer <https://www.globus.org/>`_ is our preferred route for publishing models with larger numbers or sizes of files.
If you are transfering data from your personal computer or a small research cluster, you may need to first
`install a Globus endpoint <https://www.globus.org/globus-connect>`_ on your system.
If you are transferring data directly from a high-performance computing center, Globus may already be configured and
available for use.
In either case, you may need to determine the endpoint ID of the system holding your data (see
`Endpoint Management on Globus.org <https://app.globus.org/endpoints>`_).
Once you determine the endpoint, submit your data via Globus using the CLI::

    $ dlhub publish --globus --endpoint <your endpoint ID>

Alternatively, you can allow the CLI to attempt to determine the endpoint ID::

    $ dlhub publish --globus
