import unittest
import os

from dlhub_toolbox.models.servables.sklearn import ScikitLearnModel
from dlhub_toolbox.models import __dlhub_version__


class TestSklearn(unittest.TestCase):

    def test_load_model(self):
        model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'model.pkl'))

        # Load the model
        model_info = ScikitLearnModel(model_path)
        self.assertEquals(model_info.to_dict(), {'datacite': {'creators': [], 'publisher': 'DLHub',
                                                              'titles': [None]},
                                                 "dlhub": {"version": __dlhub_version__,
                                                           "visible_to": ["public"],
                                                           "domain": None},
                                                 'servable': {'type': 'scikit-learn',
                                                              'version': '0.19.1',
                                                              'model_type': 'SVC'}})
