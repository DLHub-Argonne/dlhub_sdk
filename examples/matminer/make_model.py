from matminer.featurizers.base import MultipleFeaturizer
from matminer.featurizers import composition as cf
from matminer.datasets import dataframe_loader
from sklearn.preprocessing import Imputer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
import pickle as pkl

# Load a test dataset from matminer
data = dataframe_loader.load_flla()
print('Loaded {} rows with {} columns:'.format(len(data), len(data.columns)),
      data.columns.tolist())

# Get only the minimum energy structure at each composition
data['composition'] = data['structure'].apply(lambda x: x.composition)
data['integer_formula'] = data['composition'].apply(lambda x: x.get_integer_formula_and_factor()[0])

data.sort_values('e_above_hull', ascending=True, inplace=True)
data.drop_duplicates('integer_formula', keep='first', inplace=True)
print('Reduced dataset to {} unique compositions.'.format(len(data)))

data.reset_index(inplace=True, drop=True)

# Create the featurizer, which will take the composition as input
featurizer = MultipleFeaturizer([
      cf.Stoichiometry(),
      cf.ElementProperty.from_preset('magpie'),
      cf.ValenceOrbital(props=['frac']),
      cf.IonProperty(fast=True)
])

# Compute the features
featurizer.set_n_jobs(1)
X = featurizer.featurize_many(data['composition'])

# Make the model
model = Pipeline([
    ('imputer', Imputer()),
    ('model', RandomForestRegressor())
])
model.fit(X, data['formation_energy_per_atom'])
print('Trained a RandomForest model')

# Save the model, featurizer, and data using pickle
with open('model.pkl', 'wb') as fp:
    pkl.dump(model, fp)
with open('featurizer.pkl', 'wb') as fp:
    pkl.dump(featurizer, fp)
data.to_pickle('data.pkl')
print('Saved model components to disk')
