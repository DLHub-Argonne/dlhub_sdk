from dlhub_toolbox.models.servables.sklearn import ScikitLearnModel
from dlhub_toolbox.models.datasets import TabularDataset
import pandas as pd
import json


# Make the dataset information
dataset_info = TabularDataset('iris.csv', read_kwargs=dict(header=1))

#   Read in the dataset
data = pd.read_csv('iris.csv', header=1)

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

#    Describe the data provenance
dataset_info.set_title("Iris Dataset")
dataset_info.set_name("iris_dataset")
dataset_info.set_authors(["Marshall, R.A."])

# Make the model information
model_info = ScikitLearnModel('model.pkl', n_input_columns=len(data.columns) - 1,
                              classes=data['species'].unique())

#    Describe the model
model_info.set_title("Example Scikit-Learn Model")
model_info.set_name("iris_svm")
model_info.set_domain("biology")

# Print out the result
print('--> Dataset Information <--')
print(json.dumps(dataset_info.to_dict(), indent=2))
print('\n--> Model Information <--')
print(json.dumps(model_info.to_dict(), indent=2))
