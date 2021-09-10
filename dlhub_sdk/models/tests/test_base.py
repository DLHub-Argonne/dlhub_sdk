from dlhub_sdk.models import BaseMetadataModel


def test_dlhub_block():
    model = BaseMetadataModel()
    assert model.dlhub.visible_to == ['public']
