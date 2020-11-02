import os
from setuptools import setup, find_packages

# single source of truth for package version
version_ns = {}
with open(os.path.join("dlhub_sdk", "version.py")) as f:
    exec(f.read(), version_ns)
version = version_ns['__version__']

# Load in requirements from "requirements.txt"
with open("requirements.txt") as f:
    requirements = [x.strip() for x in f]

setup(
    name='dlhub_sdk',
    version=version,
    packages=find_packages(),
    description='Python interface and utilities for DLHub',
    long_description=("DLHub SDK contains a Python interface to the Data "
                      "and Learning Hub for Science (DLHub). These interfaces "
                      "include functions for quickly describing a model in the "
                      "correct schema for DLHub, and discovering or using models "
                      "that other scientists have published."),
    install_requires=requirements,
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
