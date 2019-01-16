Servable Publication Guide
==========================

Publishing a new servable to DLHub requires two main steps: describing the servable and submitting it.
In this guide, we provide a tutorial for describing different kinds of servables
and an overview of the routes available for sending it to DLHub.

Step 1: Preparing the Submission Directory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You will first need to install the `dlhub_cli <https://github.com/DLHub-Argonne/dlhub_cli>`_
and `dlhub_sdk <https://github.com/DLHub-Argonne/dlhub_sdk>`_ on your system.
Both libraries are on PyPi, so you can install them with::

    $ pip install dlhub_sdk dlhub_cli

The first step in the servable submission process is to authenticate with dlhub: :code:`dlhub login`

Then, use the DLHub CLI to initialize the script for describing your servable::

    $ dlhub init --author "Your, Name" "Your Affiliation" --name unique_name

The ``init`` command creates a Python script, ``describe_servable.py``, which
you edit to further describe the function of your servable.
This command requires a name, which should be different than any other
servable you have published to DLHub [#]_ and can optionally take other information
to pre-populate your description script.
Call :code:`dlhub init --help` for full details.


Step 2: Describing a Servable
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``describe_servable.py`` file created in Step 1 will generate a file, ``dlhub.json``,
that contains a short description of your servable.
You will need to edit ``describe_servable.py`` file to add enough information
for DLHub and other humans to use your servable.

Describing the Purpose and Provenance
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There are a few places in the ``describe_servable.py`` file to capture a description
of what the servable does.
As noted by the "TODO" comments in the template, we recommend for your to write
a descriptive title and short abstract about the servable as well as indicating
other resources (e.g., papers) where users can find more information.

Describing the Computational Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There are two routes for specifying environment: defining Python libraries or using ``repo2docker``.

Basic Route: Specifying Python Libraries
++++++++++++++++++++++++++++++++++++++++

The computational environment for many servables can be defined by only the required Python packages.
If this is true for your servable, edit the ``describe_servable.py`` file to include these requirements::

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
learn how to describe an environment.
Once you have created the files, edit the ``describe_servable.py`` to point to the directory containing your configuration::

    # Include repo2docker files in current directory
    model.parse_repo2docker_configuration()

    # Include repo2docker files in a different directory
    model.parse_repo2docker_configuration('../another/path')

Describing the Model
^^^^^^^^^^^^^^^^^^^^

DLHub supports numerous types of servables through different ``BaseServableModel`` tools.
Each tool builds a description for a certain type of servable (e.g., Keras model)
and has a corresponding class on the `DLHub backend <https://github.com/DLHub-Argonne/home_run>`_
that uses the description to run your servable.
Select the tool from the `Servable Types <servable-types.html>`_ documentation
that matches your servable and follow the guide for describing it.
Common examples include:

- `Generic Python Functions <servable-types.html#python-functions>`_
- Tensorflow
- Keras
- Scikit-Learn

Once finished, the ``dlhub.json`` file created by running ``describe_servable.py``
will have all the information needed by DLHub to run your model.
You can re-run ``describe_servable.py`` to update the description
if you ever make changes to the servable.

Step 3: Submitting the Model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are several routes for submitting a servable to DLHub.

Recommended: Publishing Servable to Git Repository
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Our recommended route for submitting servables to DLHub is to first publish the servable on a publicly-accessible git repository.
You will need to add the ``dlhub.json`` file to your git repository along with all files mentioned in that servable description.
For servables that require large data files (e.g., weights for deep learning models),
we recommend using `git-lfs <https://git-lfs.github.com/>`_ to include them in the repository
or `using Globus to submit the servable <#publication-via-globus>`_.

After publishing all associated file to GitHub, use the DLHub CLI to publish the repository::

    # Publish from the root folder of a git repository
    $ dlhub publish --repository https://github.com/ryanchard/dlhub_publish_example

    # Publish from another path within of a git repository
    $ dlhub publish --repository https://github.com/ryanchard/dlhub_publish_example another/path

*Note: Publication from a non-root directory is still under development*

Publication via Direct Upload
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It is also possible to submit servables directly from your computer to DLHub via HTTP::

    $ dlhub publish --local

This route is recommend for servables you do not want to share publicly and have small file sizes.

Publication via Globus
^^^^^^^^^^^^^^^^^^^^^^

*Note: This feature is under development*

`Globus Transfer <https://www.globus.org/>`_ is our preferred route for publishing servables with large numbers or sizes of files.
To publish from your personal computer, you may need to first
`install a Globus endpoint <https://www.globus.org/globus-connect>`_.
If you are publishing from a high-performance computing center, Globus may already be
configured and available for use.
In either case, you may need to determine the endpoint ID of the system holding your data (see
`Endpoint Management on Globus.org <https://app.globus.org/endpoints>`_ to find it).
Then, submit your data via Globus using the CLI::

    $ dlhub publish --globus --endpoint <your endpoint ID>

Alternatively, allow the CLI to attempt to determine the endpoint ID::

    $ dlhub publish --globus

.. [#] But can duplicate names from other users