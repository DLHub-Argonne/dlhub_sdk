from dlhub_toolbox.models.servables.python import PythonClassMethodModel
from dlhub_toolbox.models.servables.sklearn import ScikitLearnModel
from dlhub_toolbox.models.datasets import TabularDataset
import pickle as pkl
import pandas as pd
import json


# Make the dataset information
dataset_info = TabularDataset('data.pkl', format='pickle')

#   Read in the dataset
data = pd.read_pickle('data.pkl')

#   Add link to where this data was downloaded from
dataset_info.add_alternate_identifier("https://github.com/hackingmaterials/matminer/blob/master/matminer/datasets/flla_2015.csv?raw=true", "URL")

#   Add link to paper describing the dataset
dataset_info.add_related_identifier("10.1002/qua.24917.", "DOI", "IsDescribedBy")
dataset_info.add_related_identifier("http://materialsproject.org", "URL", "IsDerivedFrom")

#   Mark the domain of the dataset
dataset_info.set_domains(["materials science"])

#   Describe the columns
dataset_info.annotate_column("material_id", description="Materials Project ID number", data_type='string')
dataset_info.annotate_column("e_above_hull", description="Energy above the T=0K convex hull, a measure of stability",
                             units="eV/atom")
dataset_info.annotate_column("formula", description="Chemical formula, as a dictionary", data_type='dict')
dataset_info.annotate_column("nsites", description="Number of atoms in crystal structure")
dataset_info.annotate_column("structure", description="Crystal structure",
                             data_type="pymatgen.core.Structure")
dataset_info.annotate_column("composition", description="Composition of the crystal",
                             data_type='pymatgen.core.Composition')
dataset_info.annotate_column('integer_formula', description='Composition as a string',
                             data_type='string')
dataset_info.annotate_column('formation_energy', description='Formation energy of the structure',
                             units='eV/unit-cell')
dataset_info.annotate_column('formation_energy_per_atom', description='Formation energy of the structure',
                             units='eV/atom')

#   Mark which columns are inputs and outputs
dataset_info.mark_inputs(['integer_formula'])
dataset_info.mark_labels(['formation_energy_per_atom'])

#    Describe the data provenance
dataset_info.set_title("Formation Enthalpy of a Subset of ICSD Compounds")
dataset_info.set_name("faber_icsd_subset")
dataset_info.set_authors(["Faber, F.", "Lindmaa, A.", "von Lilienfled, O. A.", "Armiento, R."],
                         ["University of Basel", "Linkoping University",
                          ["University of Basel", "Argonne National Laboratory"],
                          "Linkoping University"])

# Describe the featurizer
with open('featurizer.pkl', 'rb') as fp:
    featurizer = pkl.load(fp)
feat_info = PythonClassMethodModel('featurizer.pkl', 'featurize_many', {'ignore_errors': True})

#   Add reference information
feat_info.set_title('Composition featurizer of Ward et al. 2016')
feat_info.set_name("ward_npj_2016_featurizer")
feat_info.set_authors(['Ward, Logan'], ['University of Chicago'])

#   Add citation information
feat_info.add_related_identifier('10.1038/npjcompumats.2016.28', 'DOI', 'IsDescribedBy')

#   Describe the software requirements
feat_info.add_requirement('matminer', 'detect')

#   Describe the inputs and outputs
feat_info.set_inputs('list', 'List of pymtagen Composition objects',
                     item_type={'type': 'python object', 'python_type': 'pymatgen.core.Composition'})
feat_info.set_outputs('ndarray', 'List of features', shape=[None, len(featurizer.feature_labels())])

# Make the model information
model_info = ScikitLearnModel('model.pkl', n_input_columns=len(featurizer.feature_labels()))

#    Describe the model
model_info.set_title("Formation enthalpy predictor")
model_info.set_name("delta-e_icsd-subset_model")
model_info.set_domains(["materials science"])

# Print out the result
print('--> Dataset Information <--')
print(json.dumps(dataset_info.to_dict(), indent=2))
print('\n--> Featurizer Information <--')
print(json.dumps(feat_info.to_dict(), indent=2))
print('\n--> Model Information <--')
print(json.dumps(model_info.to_dict(), indent=2))

# Save the models to disk for use when creating a pipeline
with open('model_info.pkl', 'wb') as fp:
    pkl.dump(model_info, fp)
with open('featurize_info.pkl', 'wb') as fp:
    pkl.dump(feat_info, fp)
