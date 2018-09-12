"""Create a pipeline that predicts formation energies of a list of strings"""

from dlhub_toolbox.models.servables.python import PythonStaticMethodModel
from dlhub_toolbox.models.pipeline import PipelineModel
from pymatgen import Composition
import pickle as pkl
import json

# Load in the model and featurizer steps
with open('featurize_info.pkl', 'rb') as fp:
    feat_info = pkl.load(fp)
with open('model_info.pkl', 'rb') as fp:
    model_info = pkl.load(fp)

# Make a new step that takes a list of strings, and returns a list of Python objects
convert_info = PythonStaticMethodModel.from_function_pointer(Composition, autobatch=True)
convert_info.set_title("Convert List of Strings to Pymatgen Composition Objects")
convert_info.set_inputs("list", "List of strings", item_type="string")
convert_info.set_outputs("list", "List of pymatgen composition objects",
                         item_type={'type': 'python object',
                                    'python_type': 'pymatgen.core.Composition'})

# Assign each step a DLHub ID
feat_info.assign_dlhub_id()
convert_info.assign_dlhub_id()
model_info.assign_dlhub_id()

# Compile them into a Pipeline
pipeline_info = PipelineModel().set_name('delta_e-predictor')
pipeline_info.set_title("Predict Formation Enthalpy from Composition")
pipeline_info.add_step(convert_info.dlhub_id, "Convert strings to pymatgen objects")
pipeline_info.add_step(feat_info.dlhub_id, "Compute features each object")
pipeline_info.add_step(model_info.dlhub_id, "Use features to compute formation enthalpy")
print(json.dumps(pipeline_info.to_dict(), indent=2))
