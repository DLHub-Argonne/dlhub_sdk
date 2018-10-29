from dlhub_sdk.models.servables.python import PythonStaticMethodModel
from dlhub_sdk.client import DLHubClient
from unittest import TestCase, skip
import pandas as pd


class TestClient(TestCase):

    def test_dlhub_init(self):
        dl = DLHubClient()
        self.assertEqual(dl.service, "https://dlhub.org/api/v1")
        self.assertIsInstance(dl, DLHubClient)

    def test_get_servables(self):
        dl = DLHubClient()
        r = dl.get_servables()
        self.assertIsInstance(r, pd.DataFrame)
        self.assertGreater(r.shape[-1], 0)
        self.assertNotEqual(r.shape[0], 0)

    def test_get_id_by_name(self):
        dl = DLHubClient()
        name = "noop"
        r = dl.get_id_by_name(name)
        r2 = dl.get_servables()
        true_val = r2["uuid"][r2["name"].tolist().index(name)]
        self.assertEqual(r, true_val)

        # Invalid name
        with self.assertRaises(IndexError):
            dl.get_id_by_name("foo")

    def test_run(self):
        dl = DLHubClient(timeout=10)
        name = "noop"
        data = {"data": ["V", "Co", "Zr"]}
        serv = dl.get_id_by_name(name)
        res = dl.run(serv, data)

        # Check the results
        self.assertIsInstance(res, pd.DataFrame)

    @skip  # Do not yet have a "test" route for submitted objects
    def test_submit(self):
        dl = DLHubClient()

        # TODO: Set the same UUID as the original test

        # Make an example function
        model = PythonStaticMethodModel.create_model('numpy.linalg', 'norm')
        model.set_name('1d_norm')
        model.set_title('Norm of a 1D Array')
        model.set_inputs('ndarray', 'Array to be normed', shape=[None])
        model.set_outputs('number', 'Norm of the array')

        # Submit the model
        dl.publish_servable(model)
