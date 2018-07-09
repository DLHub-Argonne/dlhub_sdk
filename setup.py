from setuptools import setup

setup(
    name='dlhub_toolbox',
    version='0.0.1',
    packages=['dlhub_toolbox'],
    description='Tools for submitting datasets and models to DLHub',
    long_description=("DLHub Toolbox contains scripts designed to make it easier to submit "
        "datasets and machine learning models to the Data and Learning Hub for Science (DLHub). "
        "This package contains tools for formatting descriptions of datasets and machine learning models "
        "in the format required by DLHub, and a wrapper around the API for sending them to DLHub for publication"),
    install_requires=[
        "jsonobject==0.9.1",
    ],
    python_requires=">=3.4",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering"
    ],
    keywords=[
        "DLHub",
        "Data and Learning Hub for Science",
        "machine learning",
        "data publication",
        "reproducibility",
    ],
    license="Apache License, Version 2.0",
    url="https://github.com/DLHub-Argonne/dlhub_toolbox"
)
