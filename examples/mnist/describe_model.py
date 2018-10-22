from dlhub_toolbox.models.servables.keras import KerasModel
import pickle as pkl
import json


# Describe the keras model
model_info = KerasModel.create_model('model.hd5', list(map(str, range(10))))

#    Describe the model
model_info.set_title("MNIST Digit Classifier")
model_info.set_name("mnist_tiny_example")
model_info.set_domains(["general","digit recognition"])

#    Describe the outputs in more detail
model_info.output['description'] = 'Probabilities of being 0-9'
model_info.input['description'] = 'Image of a digit'

# Print out the result
print('\n--> Model Information <--')
print(json.dumps(model_info.to_dict(), indent=2))

# Save the model information to pickle
with open('model_info.pkl', 'wb') as fp:
    pkl.dump(model_info, fp)
