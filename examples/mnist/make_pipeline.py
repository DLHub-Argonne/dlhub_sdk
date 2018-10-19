"""Create a pipeline that guesses the digit for any image"""


from dlhub_toolbox.models.servables.python import PythonStaticMethodModel
from dlhub_toolbox.models.pipeline import PipelineModel
from dlhub_toolbox.utils.types import compose_argument_block
from skimage.transform import resize
from skimage.io import imread

import pickle as pkl
import json

# Load in the model and featurizer steps

with open('model_info.pkl', 'rb') as fp:
    model_info = pkl.load(fp)

# Make a new step that reads files in from disk
read_info = PythonStaticMethodModel.from_function_pointer(imread, autobatch=True,
                                                          function_kwargs={'as_gray': True})
read_info.set_title("Read in a list of pictures to a grayscale file")
read_info.set_name("read_grayscale_image")
read_info.set_inputs("list", "List of paths to files", item_type="string")
read_info.set_outputs("list", "List of images as ndarrays",
                      item_type=compose_argument_block('ndarray', 'Image', shape=[None, None]))
read_info.add_requirement('scikit-image', 'detect')

# Make a step to reshape the to 28x28x1
resize_info = PythonStaticMethodModel.from_function_pointer(resize, autobatch=True,
                                                            function_kwargs={
                                                                'output_shape': [28, 28, 1],
                                                                'anti_aliasing': True})
resize_info.set_title("Reshape images to a specific size")
resize_info.set_name('reshape_image')
resize_info.set_inputs("list", "List of images as ndarrays",
                       item_type=compose_argument_block('ndarray', 'Image', shape=[None, None]))
resize_info.set_outputs("list", "List of images as ndarrays shaped for use in keras",
                        item_type=compose_argument_block('ndarray', 'Image', shape=[28, 28, 1]))
resize_info.add_requirement('scikit-image', 'detect')

# Assign each step a DLHub ID
read_info.assign_dlhub_id()
resize_info.assign_dlhub_id()
model_info.assign_dlhub_id()

# Compile them into a Pipeline
pipeline_info = PipelineModel().set_name('tiny_mnist_pipeline')
pipeline_info.set_title("Image File to Digit Pipeline")
pipeline_info.add_step(read_info.dlhub_id, "Read in images from disk into grayscale files")
pipeline_info.add_step(resize_info.dlhub_id, "Reshape each image into a 28x28x1 image")
pipeline_info.add_step(model_info.dlhub_id, "Determine which digit is present in the image")
print(json.dumps(pipeline_info.to_dict(), indent=2))
