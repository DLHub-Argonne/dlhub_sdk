Quickstart
==========

Welcome to the DLHub SDK. This SDK simplifies interacting with the DLHub service and the deployed servables.

Installation
------------

The SDK is available on PyPI, but first make sure you have Python3.5+

>>> python3 --version

The CLI has been tested on Linux.


Installation using Pip
^^^^^^^^^^^^^^^^^^^^^^

While ``pip`` and ``pip3`` can be used to install the CLI we suggest the following approach
for reliable installation when many Python environments are avaialble.::

     $ python3 -m pip install dlhub_sdk

     (to update a previously installed parsl to a newer version, use: python3 -m pip install -U dlhub_sdk)


Installation using Conda
^^^^^^^^^^^^^^^^^^^^^^^^
1. Install Conda and setup python3.6 following the instructions `here <https://conda.io/docs/user-guide/install/macos.html>`_::

     $ conda create --name dlhub_py36 python=3.6
     $ source activate dlhub_py36

2. Install the SDK::

     $ python3 -m pip install dlhub_sdk

     (to update a previously installed the cli to a newer version, use: python3 -m pip install -U dlhub_sdk)

For Developers
--------------

1. Download the SDK::

    $ git clone https://github.com/DLHub-Argonne/dlhub_sdk

2. Install::

    $ cd dlhub_sdk
    $ python3 setup.py install

3. Use the SDK!

Requirements
------------

DLHub_SDK requires the following:

* Python 3.5+
