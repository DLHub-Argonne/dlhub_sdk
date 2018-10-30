from setuptools import setup

setup(
    name='dlhub_sdk',
    version='0.1.0',
    packages=['dlhub_sdk'],
    description='Tools for submitting datasets and models to DLHub',
    long_description=("DLHub SDK contains utilities that simplify interacting with the Data and"
                      " Learning Hub for Science (DLHub). This package contains ans tools for"
                      " formatting descriptions of datasets and machine learning models in the"
                      " format required by DLHub, and a wrapper around the API (DLHubClient)."
                      " The DLHub client provides an easy route for publishing, discovering, and"
                      " using machine learning models in DLHub."),
    install_requires=[
        "pandas", "requests"
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
    author='Ben Blaiszik',
    author_email='bblaiszik@anl.gov',
    license="Apache License, Version 2.0",
    url="https://github.com/DLHub-Argonne/dlhub_sdk"
)
