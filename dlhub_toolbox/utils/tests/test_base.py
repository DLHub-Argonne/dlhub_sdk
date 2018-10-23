from unittest import TestCase

from dlhub_toolbox.utils import unserialize_object
from dlhub_toolbox.models.datasets import Dataset


class TestBase(TestCase):
    """Tests the general utility functions"""

    def test_unserialize(self):
        model = Dataset()
        model.set_name('test')
        model.set_title('Test')

        # Store the metadata in a dictionary without class information
        metadata = model.to_dict()
        model_copy = unserialize_object(metadata)
        self.assertEqual('BaseMetadataModel', model_copy.__class__.__name__)  # Uses the base class

        # Store the metadata in a dictionary with class information
        metadata = model.to_dict(save_class_data=True)
        model_copy = unserialize_object(metadata)
        self.assertTrue(isinstance(model_copy, Dataset))
