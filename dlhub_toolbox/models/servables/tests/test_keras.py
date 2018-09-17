from dlhub_toolbox.utils.schemas import validate_against_dlhub_schema
from dlhub_toolbox.models.servables.keras import KerasModel
from keras import __version__ as keras_version
from keras.models import Sequential, Model
from keras.layers import Dense, Input
from unittest import TestCase
from tempfile import mkdtemp
import shutil
import os


class TestKeras(TestCase):

    maxDiff = 4096

    def test_keras_single_input(self):
        # Make a Keras model
        model = Sequential()
        model.add(Dense(16, input_shape=(1,), activation='relu', name='hidden'))
        model.add(Dense(1, name='output'))
        model.compile(optimizer='rmsprop', loss='mse')

        # Save it to disk
        tempdir = mkdtemp()
        try:
            model_path = os.path.join(tempdir, 'model.hd5')
            model.save(model_path)

            # Create a model
            metadata = KerasModel(model_path)
            metadata.set_title('Keras Test')
            metadata.set_name('mlp')

            output = metadata.to_dict()
            self.assertEqual(output, {
                "datacite": {"creators": [], "titles": [{"title": "Keras Test"}],
                             "publisher": "DLHub", "publicationYear": "2018",
                             "identifier": {"identifier": "10.YET/UNASSIGNED",
                                            "identifierType": "DOI"},
                             "resourceType": {"resourceTypeGeneral": "InteractiveResource"}},
                "dlhub": {"version": "0.1", "domain": "", "visible_to": ["public"], "id": None,
                          "name": "mlp"},
                "servable": {"methods": {"run": {
                    "input": {"type": "ndarray", "description": "Tensor",
                                  "shape": [None, 1]},
                    "output": {"type": "ndarray", "description": "Tensor",
                               "shape": [None, 1]}, "parameters": {},
                    "method_details": {"method_name": "predict"}}},
                    "files": {"model": model_path, "other": []},
                    "type": "Keras Model",
                    "shim": "keras.KerasServable",
                    "language": "python",
                    "model_type": "Deep NN",
                    "model_summary": """_________________________________________________________________
Layer (type)                 Output Shape              Param #   
=================================================================
hidden (Dense)               (None, 16)                32        
_________________________________________________________________
output (Dense)               (None, 1)                 17        
=================================================================
Total params: 49
Trainable params: 49
Non-trainable params: 0
_________________________________________________________________
""",
                    "dependencies": {"python": {
                        'keras': keras_version
                    }}}})

            # Validate against schema
            validate_against_dlhub_schema(output, 'servable')
        finally:
            shutil.rmtree(tempdir)

    def test_keras_multioutput(self):
        # Make a Keras model
        input_layer = Input(shape=(4,))
        dense = Dense(16, activation='relu')(input_layer)
        output_1 = Dense(1, activation='softmax')(dense)
        output_2 = Dense(2, activation='softmax')(dense)
        model = Model([input_layer], [output_1, output_2])
        model.compile(optimizer='rmsprop', loss='mse')

        # Save it to disk
        tempdir = mkdtemp()
        try:
            model_path = os.path.join(tempdir, 'model.hd5')
            model.save(model_path)

            # Create a model
            metadata = KerasModel(model_path)
            metadata.set_title('Keras Test')
            metadata.set_name('mlp')

            self.assertEqual(metadata._get_output(),
                             {'type': 'list',
                              'description': 'List of tensors',
                              'item_type': [
                                  {'type': 'ndarray', 'description': 'Tensor', 'shape': [None, 1]},
                                  {'type': 'ndarray', 'description': 'Tensor', 'shape': [None, 2]}
                              ]})

            output = metadata.to_dict()

            # Validate against schema
            validate_against_dlhub_schema(output, 'servable')
        finally:
            shutil.rmtree(tempdir)
