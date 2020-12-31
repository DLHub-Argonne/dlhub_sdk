from datetime import datetime
import os

try:
    import keras
except ImportError:
    from tensorflow import keras
from pytest import raises

from dlhub_sdk.models.servables.keras import KerasModel
from dlhub_sdk.utils.schemas import validate_against_dlhub_schema


_year = str(datetime.now().year)


def _make_simple_model():
    model = keras.models.Sequential()
    model.add(keras.layers.Dense(16, input_shape=(1,), activation='relu', name='hidden'))
    model.add(keras.layers.Dense(1, name='output'))
    model.compile(optimizer='rmsprop', loss='mse')
    return model


def test_keras_single_input(tmpdir):
    # Make a Keras model
    model = _make_simple_model()

    # Save it to disk
    model_path = os.path.join(tmpdir, 'model.hd5')
    model.save(model_path)

    # Create a model
    metadata = KerasModel.create_model(model_path, ["y"])
    metadata.set_title('Keras Test')
    metadata.set_name('mlp')

    # Validate against schema
    output = metadata.to_dict()
    validate_against_dlhub_schema(output, 'servable')


def test_keras_multioutput(tmpdir):
    # Make a Keras model
    input_layer = keras.layers.Input(shape=(4,))
    dense = keras.layers.Dense(16, activation='relu')(input_layer)
    output_1 = keras.layers.Dense(1, activation='relu')(dense)
    output_2 = keras.layers.Dense(2, activation='softmax')(dense)
    model = keras.models.Model([input_layer], [output_1, output_2])
    model.compile(optimizer='rmsprop', loss='mse')

    # Save it to disk
    model_path = os.path.join(tmpdir, 'model.hd5')
    model.save(model_path)

    # Create a model
    metadata = KerasModel.create_model(model_path, [['y'], ['yes', 'no']])
    metadata.set_title('Keras Test')
    metadata.set_name('mlp')

    assert metadata.servable.methods['run'].output.dict(exclude_none=True) == {
        'type': 'tuple',
        'description': 'Tuple of tensors',
        'element_types': [
            {'type': 'ndarray', 'description': 'Tensor', 'shape': [None, 1]},
            {'type': 'ndarray', 'description': 'Tensor', 'shape': [None, 2]}
        ]
    }
    output = metadata.to_dict()

    # Validate against schema
    validate_against_dlhub_schema(output, 'servable')


def test_custom_layers(tmpdir):
    """Test adding custom layers to the definition"""

    # Make a simple model
    model = _make_simple_model()

    # Save it
    model_path = os.path.join(tmpdir, 'model.hd5')
    model.save(model_path)

    # Create the metadata
    metadata = KerasModel.create_model(model_path, ['y'],
                                       custom_objects={'Dense': keras.layers.Dense})
    metadata.set_title('test').set_name('test')

    # Make sure it has the custom object definitions
    assert 'Dense' in metadata.servable.options['custom_objects']

    # Validate it against DLHub schema
    validate_against_dlhub_schema(metadata.to_dict(), 'servable')

    # Test the errors
    with raises(ValueError) as exc:
        metadata.add_custom_object('BadLayer', float)
    assert 'subclass' in str(exc)


def test_multi_file(tmpdir):
    """Test adding the architecture in a different file """

    # Make a simple model
    model = _make_simple_model()

    # Save it
    model_path = os.path.join(tmpdir, 'model.hd5')
    model.save(model_path, include_optimizer=False)
    model_json = os.path.join(tmpdir, 'model.json')
    with open(model_json, 'w') as fp:
        print(model.to_json(), file=fp)
    model_yaml = os.path.join(tmpdir, 'model.yml')
    with open(model_yaml, 'w') as fp:
        print(model.to_yaml(), file=fp)
    weights_path = os.path.join(tmpdir, 'weights.hd5')
    model.save_weights(weights_path)

    # Create the metadata
    metadata = KerasModel.create_model(weights_path, ['y'], arch_path=model_path)

    # Make sure both files are included in the files list
    assert metadata.dlhub.files == {'arch': model_path, 'model': weights_path}

    # Try it with the JSON and YAML versions
    KerasModel.create_model(weights_path, ['y'], arch_path=model_json)
    KerasModel.create_model(weights_path, ['y'], arch_path=model_yaml)
