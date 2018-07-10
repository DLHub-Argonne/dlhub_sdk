from dlhub_toolbox.models import TabularDataset
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
dataset_info.annotate_column("petal_length", description="With of sepal",
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
