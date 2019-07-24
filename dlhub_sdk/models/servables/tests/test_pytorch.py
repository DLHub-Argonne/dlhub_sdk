from datetime import datetime
from tempfile import mkdtemp
import shutil
import os

from unittest import TestCase

import torch
from Net import Net

from dlhub_sdk.models.servables.pytorch import TorchModel
from dlhub_sdk.utils.schemas import validate_against_dlhub_schema
from dlhub_sdk.version import __version__

_year = str(datetime.now().year)


def _make_simple_model():
    model = Net()
    return model


class TestTorch(TestCase):
    maxDiff = 4096

    def test_torch_single_input(self):
        # Make a Keras model
        model = _make_simple_model()

        # Save it to disk
        tempdir = mkdtemp()
        try:
            model_path = os.path.join(tempdir, 'model.pt')
            torch.save(model, model_path)

            # Create a model
            metadata = TorchModel.create_model(model_path, (2, 4), (3, 5))
            metadata.set_title('Torch Test')
            metadata.set_name('mlp')

            output = metadata.to_dict()
            self.assertEqual(output, {
                "datacite": {"creators": [], "titles": [{"title": "Torch Test"}],
                             "publisher": "DLHub", "publicationYear": _year,
                             "identifier": {"identifier": "10.YET/UNASSIGNED",
                                            "identifierType": "DOI"},
                             "resourceType": {"resourceTypeGeneral": "InteractiveResource"},
                             "descriptions": [],
                             "fundingReferences": [],
                             "relatedIdentifiers": [],
                             "alternateIdentifiers": [],
                             "rightsList": []},
                "dlhub": {"version": __version__, "domains": [],
                          "visible_to": ["public"],
                          'type': 'servable',
                          "name": "mlp", "files": {"model": model_path},
                          "dependencies": {"python": {
                              'torch': torch.__version__
                          }}},
                "servable": {"methods": {"run": {
                    "input": {"type": "ndarray", "description": "Tensor", "shape": [2, 4]},
                    "output": {"type": "ndarray", "description": "Tensor",
                               "shape": [3, 5]}, "parameters": {},
                    "method_details": {
                        "method_name": "predict"
                    }}},
                    "type": "Torch Model",
                    "shim": "torch.TorchServable",
                    "model_type": "Deep NN",
                    "model_summary": """Net(
  (conv1): Conv2d(1, 20, kernel_size=(5, 5), stride=(1, 1))
  (conv2): Conv2d(20, 50, kernel_size=(5, 5), stride=(1, 1))
  (fc1): Linear(in_features=800, out_features=500, bias=True)
  (fc2): Linear(in_features=500, out_features=10, bias=True)
)"""}})

            # Validate against schema
            validate_against_dlhub_schema(output, 'servable')
        finally:
            shutil.rmtree(tempdir)
