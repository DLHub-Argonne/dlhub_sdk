# DLHub SDK
[![Build Status](https://travis-ci.com/DLHub-Argonne/dlhub_sdk.svg?branch=master)](https://travis-ci.com/DLHub-Argonne/dlhub_sdk)
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

#### Describe the Training Set

The first step is to describe the training data, which we assume is in a `csv` file named `iris.csv`. 
The `iris.csv` file looks something like

```text
# Data from: https://archive.ics.uci.edu/ml/datasets/Iris
sepal_length,sepal_width,petal_length,petal_width,species
5.1,3.5,1.4,0.2,setosa
4.9,3.0,1.4,0.2,setosa
4.7,3.2,1.3,0.2,setosa
```

To make this dataset usable for others, we want to tell them how to read it and what the columns are.
Also, to make sure the authors of the data can be properly recognized, we need to provide provenance information.
`dlhub_sdk` provides a simple tool for specifying this information: `TabularDataset`.

```python
from dlhub_sdk.models.datasets import TabularDataset
import pandas as pd
import json

# Read in the dataset
data = pd.read_csv('iris.csv', header=1)

# Make the dataset information
dataset_info = TabularDataset.create_model('iris.csv', read_kwargs=dict(header=1))

#   Add link to where this data was downloaded from
dataset_info.add_alternate_identifier("https://archive.ics.uci.edu/ml/datasets/Iris", "URL")

#   Add link to paper describing the dataset
dataset_info.add_related_identifier("10.1111/j.1469-1809.1936.tb02137.x", "DOI", "IsDescribedBy")

#   Mark the domain of the dataset
dataset_info.set_domains(["biology"])

#   Describe the columns
dataset_info.annotate_column("sepal_length", description="Length of sepal", units="cm")
dataset_info.annotate_column("sepal_width", description="Width of sepal", units="cm")
dataset_info.annotate_column("petal_length", description="Length of petal", units="cm")
dataset_info.annotate_column("petal_width", description="Width of petal", units="cm")
dataset_info.annotate_column("species", description="Species", data_type='string')

#   Mark which columns are inputs and outputs
dataset_info.mark_inputs(data.columns[:-1])
dataset_info.mark_labels(data.columns[-1:])

# Describe the data provenance
dataset_info.set_title("Iris Dataset")
dataset_info.set_name("iris_dataset")
dataset_info.set_authors(["Marshall, R.A."])

# Print out the result
print(json.dumps(dataset_info.to_dict(), indent=2))
```

After running this script, the model produces a simple JSON description of the dataset that we will send to DLHub.

```json
{
  "datacite": {
    "creators": [
      {
        "givenName": "R.A.",
        "familyName": "Marshall",
        "affiliations": []
      }
    ],
    "titles": [
      {
        "title": "Iris Dataset"
      }
    ],
    "publisher": "DLHub",
    "publicationYear": "2018",
    "relatedIdentifiers": [
      {
        "relatedIdentifier": "10.1111/j.1469-1809.1936.tb02137.x",
        "relatedIdentifierType": "DOI",
        "relationType": "IsDescribedBy"
      }
    ],
    "alternateIdentifiers": [
      {
        "alternateIdentifier": "https://archive.ics.uci.edu/ml/datasets/Iris",
        "alternateIdentifierType": "URL"
      }
    ],
    "identifier": {
      "identifier": "10.YET/UNASSIGNED",
      "identifierType": "DOI"
    },
    "resourceType": {
      "resourceTypeGeneral": "Dataset"
    }
  },
  "dlhub": {
    "version": "0.1",
    "domains": ["biology"],
    "visible_to": [
      "public"
    ],
    "id": null,
    "name": "iris_dataset",
    "files": {
        "data": "iris.csv",
        "other": []
    }
  },
  "dataset": {
    "format": "csv",
    "read_options": {
      "header": 1
    },
    "columns": [
      {
        "name": "sepal_length",
        "type": "float",
        "units": "cm",
        "description": "Length of sepal"
      },
      {
        "name": "sepal_width",
        "type": "float",
        "description": "Width of sepal",
        "units": "cm"
      },
      {
        "name": "petal_length",
        "type": "float",
        "description": "Length of petal",
        "units": "cm"
      },
      {
        "name": "petal_width",
        "type": "float",
        "description": "Width of petal",
        "units": "cm"
      },
      {
        "name": "species",
        "type": "string",
        "description": "Species"
      }
    ],
    "inputs": [
      "sepal_length",
      "sepal_width",
      "petal_length",
      "petal_width"
    ],
    "labels": [
      "species"
    ]
  }
}
```

Note that the SDK automatically put the metadata in DataCite format and includes data automatically pulled from the dataset (e.g., that the inputs are floats).

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


#### Project Support
This material is based upon work supported by Laboratory Directed Research and Development (LDRD) funding from Argonne National Laboratory, provided by the Director, Office of Science, of the U.S. Department of Energy under Contract No. DE-AC02-06CH11357.

