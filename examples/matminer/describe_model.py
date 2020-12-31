from dlhub_sdk.models.servables.python import PythonClassMethodModel
from dlhub_sdk.models.servables.sklearn import ScikitLearnModel
import pickle as pkl
import json

# Describe the featurizer
with open('featurizer.pkl', 'rb') as fp:
    featurizer = pkl.load(fp)
feat_info = PythonClassMethodModel.create_model('featurizer.pkl',
                                                'featurize_many', {'ignore_errors': True})

#   Add reference information
feat_info.set_title('Composition featurizer of Ward et al. 2016')
feat_info.set_name("ward_npj_2016_featurizer")
feat_info.set_creators(['Ward, Logan'], ['University of Chicago'])

#   Add citation information
feat_info.add_related_identifier('10.1038/npjcompumats.2016.28', 'DOI', 'IsDescribedBy')

#   Describe the software requirements
feat_info.add_requirement('matminer', 'detect')

#   Describe the inputs and outputs
feat_info.set_inputs('list', 'List of pymtagen Composition objects',
                     item_type={'type': 'python object',
                                'python_type': 'pymatgen.core.Composition'})
feat_info.set_outputs('ndarray', 'List of features', shape=[None, len(featurizer.feature_labels())])

# Make the model information
model_info = ScikitLearnModel.create_model('model.pkl',
                                           n_input_columns=len(featurizer.feature_labels()))

#    Describe the model
model_info.set_title("Formation enthalpy predictor")
model_info.set_name("delta-e_icsd-subset_model")
model_info.set_domains(["materials science"])

# Print out the result
print('--> Featurizer Information <--')
print(json.dumps(feat_info.to_dict(), indent=2))
print('\n--> Model Information <--')
print(json.dumps(model_info.to_dict(), indent=2))
