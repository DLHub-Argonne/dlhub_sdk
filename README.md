# DLHub Toolbox
[![Build Status](https://travis-ci.org/DLHub-Argonne/dlhub_toolbox.svg?branch=master)](https://travis-ci.org/DLHub-Argonne/dlhub_toolbox)[![Coverage Status](https://coveralls.io/repos/github/DLHub-Argonne/dlhub_toolbox/badge.svg?branch=master)](https://coveralls.io/github/DLHub-Argonne/dlhub_toolbox?branch=master)

DLHub Toolbox contains scripts designed to make it easier to submit datasets and machine learning models to the Data and Learning Hub for Science (DLHub). This package contains tools for formatting descriptions of datasets and machine learning models in the format required by DLHub, and a wrapper around the API for sending them to DLHub for publication.

## Installation

`dlhub_toolbox` is not yet on PyPi. So, you have to install it by first cloning the repository and then calling `pip install -e .`

## Example Usage

As a simple example, we will show how to submit a machine learning model created based on the [Iris Dataset](https://archive.ics.uci.edu/ml/datasets/Iris).
Full scripts for this example model are in [/examples/iris](./examples/iris).

### Describe the Training Set

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
`dlhub_toolbox` provides a simple tool for specifying this information: `TabularDataset`.

```python
from dlhub_toolbox.models.datasets import TabularDataset
import pandas as pd
import json

# Read in the dataset
data = pd.read_csv('iris.csv', header=1)

# Make the dataset information
dataset_info = TabularDataset('iris.csv', read_kwargs=dict(header=1))

#   Describe the columns
dataset_info.annotate_column("sepal_length", description="Length of sepal",
                             units="cm", data_type="scalar")
dataset_info.annotate_column("sepal_width", description="Width of sepal",
                             units="cm", data_type="scalar")
dataset_info.annotate_column("petal_length", description="Length of petal",
                             units="cm", data_type="scalar")
dataset_info.annotate_column("petal_length", description="Width of petal",
                             units="cm", data_type="scalar")
dataset_info.annotate_column("species", description="species", data_type="string")

#   Mark which columns are inputs and outputs
dataset_info.mark_inputs(data.columns[:-1])
dataset_info.mark_labels(data.columns[-1:])

# Describe the data provenance
dataset_info.set_title("Iris Dataset")
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
    "title": "Iris Dataset"
  },
  "dataset": {
    "path": "/home/ml_user/dlhub_toolbox/examples/iris/iris.csv",
    "format": "csv",
    "read_options": {
      "header": 1
    },
    "columns": [
      {
        "name": "sepal_length",
        "description": "Length of sepal",
        "data_type": "scalar",
        "units": "cm"
      },
      {
        "name": "sepal_width",
        "description": "Width of sepal",
        "data_type": "scalar",
        "units": "cm"
      },
      {
        "name": "petal_length",
        "description": "Length of petal",
        "data_type": "scalar",
        "units": "cm"
      },  
      {
        "name": "petal_width",
        "description": "Width of petal",
        "data_type": "scalar",
        "units": "cm"
      },
      {
        "name": "species",
        "description": "species",
        "data_type": "string"
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
