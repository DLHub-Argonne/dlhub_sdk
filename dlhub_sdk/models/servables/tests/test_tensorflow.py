"""Testing the tensorflow adaptor"""
from unittest import TestCase
import tensorflow as tf
import shutil
import os

from dlhub_sdk.models.servables.tensorflow import TensorFlowModel
from dlhub_sdk.utils.schemas import validate_against_dlhub_schema

tf_export_path = os.path.join(os.path.dirname(__file__), 'tf-model')


class TestTensorflow(TestCase):

    maxDiff = 4096

    def setUp(self):
        # Clear existing model
        if os.path.isdir(tf_export_path):
            shutil.rmtree(tf_export_path)

    def make_model(self):

        tf.reset_default_graph()

        with tf.Session() as sess:

            # Make two simple graphs, both of which will be served by TF
            x = tf.placeholder('float', shape=(None, 3), name='Input')
            z = tf.placeholder('float', shape=(), name='ScalarMultiple')
            y = x + 1
            len_fun = tf.reduce_sum(y - x)  # Returns the number of elements in the array
            scale_mult = tf.multiply(z, x, name='scale_mult')

            # Create the tool for saving the model to disk
            builder = tf.saved_model.builder.SavedModelBuilder(tf_export_path)

            #  Make descriptions for the inputs and outputs
            x_desc = tf.saved_model.utils.build_tensor_info(x)
            y_desc = tf.saved_model.utils.build_tensor_info(y)
            z_desc = tf.saved_model.utils.build_tensor_info(z)
            len_fun_desc = tf.saved_model.utils.build_tensor_info(len_fun)
            scale_mult_desc = tf.saved_model.utils.build_tensor_info(scale_mult)

            #  Make a signature for the functions to be served
            func_sig = tf.saved_model.signature_def_utils.build_signature_def(
                inputs={'x': x_desc},
                outputs={'y': y_desc},
                method_name='run'
            )
            len_sig = tf.saved_model.signature_def_utils.build_signature_def(
                inputs={'x': x_desc},
                outputs={'len': len_fun_desc},
                method_name='length'
            )
            mult_sig = tf.saved_model.signature_def_utils.build_signature_def(
                inputs={'x': x_desc, 'z': z_desc},
                outputs={'scale_mult': scale_mult_desc},
                method_name='scalar_multiply'
            )

            #  Add the functions and the  state of the graph to the builder
            builder.add_meta_graph_and_variables(
                sess, [tf.saved_model.tag_constants.SERVING],
                signature_def_map={
                    tf.saved_model.signature_constants.DEFAULT_SERVING_SIGNATURE_DEF_KEY: func_sig,
                    'length': len_sig,
                    'scalar_multiply': mult_sig
                })

            #  Save the function
            builder.save()

    def test_tf(self):
        # Make a model and save it to disk
        self.make_model()

        # Create the description
        model = TensorFlowModel.create_model(tf_export_path).set_title('TF Test')\
            .set_name('tf-test')

        # Generate the metadata for the test
        metadata = model.to_dict(simplify_paths=True)

        # Check whether the 'x' is listed first for the multiple-input model or second
        self.assertEqual({'other': ['saved_model.pb']}, metadata['dlhub']['files'])
        self.assertEqual(metadata['servable'],
                         {'methods':
                             {'run': {
                                 'input': {'type': 'ndarray', 'description': 'x',
                                           'shape': [None, 3], 'item_type': {'type': 'float'}},
                                 'output': {'type': 'ndarray', 'description': 'y',
                                            'shape': [None, 3], 'item_type': {'type': 'float'}},
                                 'parameters': {},
                                 'method_details': {'input_nodes': ['Input:0'],
                                                    'output_nodes': ['add:0']}
                             }, 'length': {
                                 'input': {'type': 'ndarray', 'description': 'x',
                                           'shape': [None, 3], 'item_type': {'type': 'float'}},
                                 'output': {'type': 'float', 'description': 'len'},
                                 'parameters': {},
                                 'method_details': {'input_nodes': ['Input:0'],
                                                    'output_nodes': ['Sum:0']}
                             }, 'scalar_multiply': {
                                 'input': {'type': 'list', 'description': 'Arguments',
                                           'item_type': [
                                               {'type': 'ndarray', 'description': 'x',
                                                'shape': [None, 3], 'item_type': {'type': 'float'}},
                                               {'type': 'float', 'description': 'z'}
                                           ]},
                                 'output': {'type': 'ndarray', 'description': 'scale_mult',
                                            'shape': [None, 3], 'item_type': {'type': 'float'}},
                                 'parameters': {},
                                 'method_details': {'input_nodes': ['Input:0', 'ScalarMultiple:0'],
                                                    'output_nodes': ['scale_mult:0']}
                             }},
                             'shim': 'tensorflow.TensorFlowServable',
                             'type': 'TensorFlow Model',
                             'dependencies': {'python': {'tensorflow': tf.__version__}}})

        validate_against_dlhub_schema(metadata, 'servable')
