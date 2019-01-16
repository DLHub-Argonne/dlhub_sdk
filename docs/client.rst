Guide to DLHubClient
====================

The `DLHubClient <source/dlhub_sdk.html#dlhub_sdk.client.DLHubClient>`_
provides a Python wrapper around the web interface for DLHub.
In this part of the guide, we describe how to use the client to publish,
discover, and use servables.

Authorization
-------------

DLHub uses GlobusAuth to control access to the web services and provide
identities to each of our users.
Before creating the DLHubClient, you must log in to Globus::

    from dlhub_sdk.client import DLHubClient
    client = DLHubClient.login()

The ``login`` class method stores your credentials in your home directory
(``~/.globus.cfg``) so that you will only need to log in to Globus once when
using the client or the DLHub CLI.


Call the ``logout`` function to remove access to DLHub from your system::

    from dlhub_sdk.utils.auth import logout
    logout()

``logout`` removes the credentials from your hard disk and revokes
their authorization to prevent further use.

Publishing Servables
--------------------

The DLHubClient provides several routes for publishing servables to DLHub.
The first is to request DLHub to publish from a GitHub repository::

    client.publish_repository('https://github.com/DLHub-Argonne/example-repo.git')

There are also functions for publishing a model stored on the local system.
In either case, you must first create a ``BaseServableModel`` describing your
servable or load in an existing one from disk::

    from dlhub_sdk.utils import unserialize_object
    with open('dlhub.json') as fp:
        model = unserialize_object(json.load(fp))

Then, submit the model via HTTP by calling::

    client.publish_servable(model)

See the `Publication Guide <servable-publication.html>`_ for details on how
to describe a servable.


Discovering Models
------------------

*TBD: Waiting for updated search index. Will cover searching and getting descriptions*


Running Models
--------------

The `BaseClient.run <source/dlhub_sdk.html#dlhub_sdk.client.DLHubClient.run>`_
command runs servables published through DLHub.
To invoke the servable, you need to know the name of the servable and the username
of the owner::

    client.run(username, model_name, x)

By default, the data (``x``) is sent to DLHub after serializing it into JSON.
You can also send the data as Python objects by changing the input type::

    client.run(username, model_name, x, input_type='python')

The client will use ``pickle`` to send the input data to DLHub in this case,
allowing for a broader range of data types to be used as inputs.
