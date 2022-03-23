# DLHub SDK
[![CI](https://github.com/DLHub-Argonne/dlhub_sdk/actions/workflows/CI.yml/badge.svg)](https://github.com/DLHub-Argonne/dlhub_sdk/actions/workflows/CI.yml)
[![Coverage Status](https://coveralls.io/repos/github/DLHub-Argonne/dlhub_sdk/badge.svg?branch=master)](https://coveralls.io/github/DLHub-Argonne/dlhub_sdk?branch=master)
[![PyPI version](https://badge.fury.io/py/dlhub-sdk.svg)](https://badge.fury.io/py/dlhub-sdk)
[![Documentation Status](https://readthedocs.org/projects/dlhub-sdk/badge/?version=latest)](https://dlhub-sdk.readthedocs.io/en/latest/?badge=latest)

DLHub SDK contains a Python interface to [the Data and Learning Hub for Science (DLHub)](https://www.dlhub.org). 
These interfaces include functions for quickly describing a model in the correct schema for DLHub, and discovering or using models that other scientists have published.

## Installation

DLHub SDK is on PyPi, and can be installed using pip

```
pip install dlhub-sdk
```

## Documentation

The full documentation for `dlhub_sdk` is avilable on [Read the Docs](https://dlhub-sdk.readthedocs.io/en/latest/)

## Example Usage

The following sections are short introductions to using the DLHub SDK.

### Discovering and Running Models

Users interact with DLHub by submitting HTTP requests to a REST API. 
In an effort to make using this API simple, the DLHub SDK contains a client that provides a Python API to these requests and hides the tedious operations involved in making an HTTP call from Python.

To create the client, call

```python
from dlhub_sdk.client import DLHubClient

client = DLHubClient()
```

The client makes it simple to find interesting machine learning models. 
For example, you can get all of the models on DLHub by 

```python
d = client.get_servables()
```

That command will return a Pandas DataFrame of models, which looks something like:

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>name</th>
      <th>description</th>
      <th>id</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>mnist_tiny_example</td>
      <td>MNIST Digit Classifier with a small NN</td>
      <td>123</td>
    </tr>
    <tr>
      <th>1</th>
      <td>mnist</td>
      <td>CNN acheiving 99.25% on the MNIST test data</td>
      <td>111</td>
    </tr>
    <tr>
      <th>2</th>
      <td>formation_energy</td>
      <td>Predict the formation enthalpy of a material given its composition</td>
      <td>112</td>
    </tr>
  </tbody>
</table>

Once you get the name of a model, it can be run thorugh the client as well:

```python
client.run('ryan_globusid/noop', inputs='my data')
```

### Publishing a Model

As a simple example, we will show how to submit a machine learning model created based on the [Iris Dataset](https://archive.ics.uci.edu/ml/datasets/Iris).
Full scripts for this example model are in [/examples/iris](./examples/iris).

#### Describe the Model

For brevity, we will upload much less metadata about a model created using Scikit-Learn.

We simply load in a Scikit-Learn model from a pickle file, and then provide a minimal amount of information about it.

```python
from dlhub_sdk.models.servables.sklearn import ScikitLearnModel

model_info = ScikitLearnModel.create_model('model.pkl', n_input_columns=len(data.columns) - 1,
                                           classes=data['species'].unique())

#    Describe the model
model_info.set_title("Example Scikit-Learn Model")
model_info.set_name("iris_svm")
model_info.set_domains(["biology"])
```

The SDK will inspect the pickle file to determine the type of the model and the version of scikit-learn that was used to create it.

```json
{
  "datacite": {
    "creators": [],
    "titles": [
      {
        "title": "Example Scikit-Learn Model"
      }
    ],
    "publisher": "DLHub",
    "publicationYear": "2018",
    "identifier": {
      "identifier": "10.YET/UNASSIGNED",
      "identifierType": "DOI"
    },
    "resourceType": {
      "resourceTypeGeneral": "InteractiveResource"
    }
  },
  "dlhub": {
    "version": "0.1",
    "domains": ["biology"],
    "visible_to": [
      "public"
    ],
    "id": null,
    "name": "iris_svm",
    "files": {
        "model": "model.pkl",
        "other": []
    },
    "dependencies": {
      "python": {
        "scikit-learn": "0.19.1"
      }
    }
  },
  "servable": {
    "methods": {
      "run": {
        "input": {
          "type": "ndarray",
          "description": "List of records to evaluate with model. Each record is a list of 4 variables.",
          "shape": [
            null,
            4
          ],
          "item_type": {
            "type": "float"
          }
        },
        "output": {
          "type": "ndarray",
          "description": "Probabilities for membership in each of 3 classes",
          "shape": [
            null,
            3
          ],
          "item_type": {
            "type": "float"
          }
        },
        "parameters": {},
        "method_details": {
          "method_name": "_predict_proba"
        }
      }
    },
    "shim": "sklearn.ScikitLearnServable",
    "type": "Scikit-learn estimator",
    "model_type": "SVC",
    "model_summary": "SVC(C=1, cache_size=200, class_weight=None, coef0=0.0,\n  decision_function_shape='ovr', degree=3, gamma='auto', kernel='linear',\n  max_iter=-1, probability=True, random_state=None, shrinking=True,\n  tol=0.001, verbose=False)",
    "options": {
      "serialization_method": "pickle",
      "is_classifier": true,
      "classes": [
        "setosa",
        "versicolor",
        "virginica"
      ]
    }
  }
}
```

At this point, we are ready to publish both the model and dataset on DLHub.

#### Publishing to DLHub

You can publish a model to DLHub by first reading in the metadata from file and then calling the client:

```python
from dlhub_sdk.models import BaseMetadataModel
from dlhub_sdk.client import DLHubClient
import json

# Read the model description
with open('model.json') as fp:
    model = BaseMetadataModel.from_dict(json.load(fp)) 

# Publish the model to DLHub
client = DLHubClient()
client.publish_servable(model)
print('Model published to DLHub. ID:', model.dlhub_id)
```

When you call this script, the DLHub client will assign your model a unique identifier and the model will soon be available for you to use via DLHub.


## Project Support
This material is based upon work supported by Laboratory Directed Research and Development (LDRD) funding from Argonne National Laboratory, provided by the Director, Office of Science, of the U.S. Department of Energy under Contract No. DE-AC02-06CH11357.

