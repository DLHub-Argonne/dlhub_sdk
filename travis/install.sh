#!/bin/bash

# Update the build environment
pip install --upgrade pip setuptools wheel

# Install mandatory packages
pip install -e .
pip install coveralls flake8

# Install the packages required for tests
pip install -r test-requirements.txt
pip install -r example-requirements.txt

# Adding keras, an optional dependency
if [ ! -z "$KERAS_VERSION" ]; then
  pip install keras==$KERAS_VERSION "tensorflow<2"
fi

# Manually-specifying the version of scikit-learn
if [ ! -z "$SKLEARN_VERSION" ]; then
  pip install scikit-learn==$SKLEARN_VERSION
fi
