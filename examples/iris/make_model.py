from sklearn.svm import SVC
import pickle as pkl
import pandas as pd

# Load the data
data = pd.read_csv('iris.csv', header=1)
print('Loaded {} rows with {} columns:'.format(len(data), len(data.columns)),
      data.columns.tolist())

# Make the model
model = SVC(kernel='linear', C=1)
model.fit(data.values[:, :-1], data.values[:, -1])
print('Trained a SVC model')

# Save the model using pickle
with open('model.pkl', 'wb') as fp:
      pkl.dump(model, fp)
print('Saved model to disk')

