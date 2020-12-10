from dlhub_sdk.models.servables.sklearn import ScikitLearnModel
import pandas as pd
import json

# Read in the training data
data = pd.read_csv('iris.csv', header=1)

# Make the model information
model_info = ScikitLearnModel.create_model('model.pkl', n_input_columns=len(data.columns) - 1,
                                           classes=data['species'].unique())

#    Describe the model
model_info.set_title("Example Scikit-Learn Model")
model_info.set_name("iris_svm")
model_info.set_domains(["biology"])

# Print out the result
print(json.dumps(model_info.to_dict(), indent=2))
