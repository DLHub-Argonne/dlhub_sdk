from datetime import datetime
import os

import torch
from torch import nn
from Net import Net

from dlhub_sdk.models.servables.pytorch import TorchModel
from dlhub_sdk.utils.schemas import validate_against_dlhub_schema
from dlhub_sdk.version import __version__

_year = str(datetime.now().year)


def _make_simple_model():
    model = Net()
    return model


class MultiNetwork(nn.Module):

    def __init__(self):
        super().__init__()
        self.layer = nn.Linear(4, 1)

    def forward(self, x, y):
        return self.layer(x), self.layer(y)


def test_torch_single_input(tmpdir):
    # Make a Keras model
    model = _make_simple_model()

    # Save it to disk
    model_path = os.path.join(tmpdir, 'model.pt')
    torch.save(model, model_path)

    # Create a model
    metadata = TorchModel.create_model(model_path, (2, 4), (3, 5))
    metadata.set_title('Torch Test')
    metadata.set_name('mlp')

    output = metadata.to_dict()
    assert output["dlhub"] == {
        "version": __version__, "domains": [],
        "visible_to": [],
        'type': 'servable',
        "name": "mlp", "files": {"model": model_path},
        "dependencies": {"python": {
            'torch': torch.__version__
        }}
    }
    print("\n" + output["servable"]["model_summary"])
    assert output["servable"] == {

        "methods": {"run": {
            "input": {"type": "ndarray", "description": "Tensor", "shape": [2, 4],
                      "item_type": {"type": "float"}},
            "output": {"type": "ndarray", "description": "Tensor",
                       "shape": [3, 5], "item_type": {"type": "float"}}, "parameters": {},
            "method_details": {
                "method_name": "__call__"
            }}},
        "type": "Torch Model",
        "shim": "torch.TorchServable",
        "model_type": "Deep NN",
        "model_summary": """Net(
  (conv1): Conv2d(1, 20, kernel_size=(5, 5), stride=(1, 1))
  (conv2): Conv2d(20, 50, kernel_size=(5, 5), stride=(1, 1))
  (fc1): Linear(in_features=800, out_features=500, bias=True)
  (fc2): Linear(in_features=500, out_features=10, bias=True)
)""",
        "options": {}
    }

    # Validate against schema
    validate_against_dlhub_schema(output, 'servable')


def test_multinetwork(tmpdir):
    model = MultiNetwork()

    model_path = os.path.join(tmpdir, 'model.pth')
    torch.save(model, model_path)

    metadata = TorchModel.create_model(model_path, [(None, 4)]*2, [(None, 1)]*2,
                                       input_type='float', output_type=['float', 'float'])
    metadata.set_name('t').set_title('t')

    # Test the output shapes
    assert metadata.servable.methods['run'].input.dict(exclude_none=True) == {
        'type': 'tuple', 'description': 'Tuple of tensors',
        'element_types': [{'type': 'ndarray',
                           'description': 'Tensor', 'shape': [None, 4],
                           'item_type': {'type': 'float'}},
                          {'type': 'ndarray',
                           'description': 'Tensor', 'shape': [None, 4],
                           'item_type': {'type': 'float'}}]}
    assert metadata.servable.methods["run"].output.dict(exclude_none=True) == {
        'type': 'tuple', 'description': 'Tuple of tensors',
        'element_types': [{'type': 'ndarray',
                           'description': 'Tensor', 'shape': [None, 1],
                           'item_type': {'type': 'float'}},
                          {'type': 'ndarray',
                           'description': 'Tensor', 'shape': [None, 1],
                           'item_type': {'type': 'float'}}]}

    validate_against_dlhub_schema(metadata.to_dict(), 'servable')
