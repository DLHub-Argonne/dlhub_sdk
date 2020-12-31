"""Testing the tensorflow adaptor"""
import tensorflow as tf
import shutil
import os

from pytest import fixture

from dlhub_sdk.models.servables.tensorflow import TensorFlowModel
from dlhub_sdk.utils.schemas import validate_against_dlhub_schema

# Do not write to a temp directory so I can see it outside of tests
tf_export_path = os.path.join(os.path.dirname(__file__), 'tf-model')


def _make_model_v1():
    """Builds a graph and exports it using SavedModel"""
    tf.reset_default_graph()

    with tf.Session() as sess:
        # Make two simple graphs, both of which will be served by TF
        x = tf.placeholder('float', shape=(None, 3), name='Input')
        z = tf.placeholder('float', shape=(), name='ScalarMultiple')
        m = tf.Variable([1.0, 1.0, 1.0], name='Slopes')
        y = m * x + 1
        len_fun = tf.reduce_sum(y - x)  # Returns the number of elements in the array
        scale_mult = tf.multiply(z, x, name='scale_mult')

        # Initialize the variables
        init = tf.global_variables_initializer()
        sess.run(init)

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


def _make_model_v2():
    """Builds and saves a custom module"""
    class CustomModule(tf.Module):

        def __init__(self):
            super().__init__()
            self.m = tf.Variable([1.0, 1.0, 1.0], name='slope')

        @tf.function
        def __call__(self, x):
            y = self.m * x + 1
            return y

        @tf.function(input_signature=[tf.TensorSpec((None, 3), tf.float32)])
        def length(self, x):
            return tf.reduce_sum(self(x) - x, name='length')

        @tf.function(input_signature=[tf.TensorSpec([], tf.float32),
                                      tf.TensorSpec((None, 3), tf.float32)])
        def scalar_multiply(self, z, x):
            return tf.multiply(z, x, name='scale_mult')

    module = CustomModule()

    # Make a concrete version of __call__
    call = module.__call__.get_concrete_function(tf.TensorSpec((None, 3)))

    tf.saved_model.save(
        module, tf_export_path, signatures={
            tf.saved_model.DEFAULT_SERVING_SIGNATURE_DEF_KEY: call,
            'length': module.length,
            'scalar_multiply': module.scalar_multiply
        }
    )


@fixture(autouse=True)
def setUp():
    # Clear existing model
    if os.path.isdir(tf_export_path):
        shutil.rmtree(tf_export_path)


def test_tf():
    # Make a model and save it to disk
    if tf.__version__ < '2':
        _make_model_v1()
    else:
        _make_model_v2()

    # Create the description
    model = TensorFlowModel.create_model(tf_export_path).set_title('TF Test')\
        .set_name('tf-test')

    # Generate the metadata for the test
    metadata = model.to_dict(simplify_paths=True)

    # Make sure the files are there
    my_files = metadata['dlhub']['files']['other']
    assert 'saved_model.pb' in my_files
    assert os.path.join('variables', 'variables.data-00000-of-00001') in my_files
    assert os.path.join('variables', 'variables.index') in my_files

    # Check the tensorflow version
    assert metadata['dlhub']['dependencies'] == {'python': {'tensorflow': tf.__version__}}

    # Check whether the 'x' is listed first for the multiple-input model or second
    my_methods = metadata['servable']['methods']
    assert my_methods['run']['input']['type'] == 'ndarray'
    assert my_methods['run']['input']['shape'] == [None, 3]
    assert my_methods['run']['input']['item_type'] == {'type': 'float'}

    assert my_methods['scalar_multiply']['input']['type'] == 'tuple'
    assert my_methods['scalar_multiply']['input']['element_types'][0]['shape'] == [None, 3]
    assert my_methods['scalar_multiply']['input']['element_types'][1]['shape'] == []

    assert 'length' in my_methods
    assert 'scalar_multiply' in my_methods

    # Check the shim
    assert metadata['servable']['shim'] == 'tensorflow.TensorFlowServable'

    validate_against_dlhub_schema(metadata, 'servable')
