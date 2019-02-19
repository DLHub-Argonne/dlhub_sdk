import pandas as pd
from unittest import TestCase, skip

from dlhub_sdk.models.servables.python import PythonStaticMethodModel
from dlhub_sdk.client import DLHubClient


class TestClient(TestCase):

    def setUp(self):
        self.dl = DLHubClient(http_timeout=10)

    def test_dlhub_init(self):
        self.assertIsInstance(self.dl, DLHubClient)

    def test_get_servables(self):
        r = self.dl.get_servables()
        self.assertIsInstance(r, list)
        self.assertIn('dlhub', r[0])

        # Make sure there are no duplicates
        self.assertEqual(len(r), len(set(i['dlhub']['shorthand_name'] for i in r)))

        # Get with all versions of the model
        r = self.dl.get_servables(False)
        self.assertNotEqual(len(r), len(set(i['dlhub']['shorthand_name'] for i in r)))

    def test_run(self):
        user = "ryan_globusid"
        name = "noop"
        data = {"data": ["V", "Co", "Zr"]}

        # Test sending the data as JSON
        res = self.dl.run("{}/{}".format(user, name), data, input_type='json')
        self.assertEqual({}, res)

        # Test sending the data as pickle
        res = self.dl.run("{}/{}".format(user, name), data, input_type='python')
        self.assertEqual({}, res)

    @skip
    def test_submit(self):
        # Make an example function
        model = PythonStaticMethodModel.create_model('numpy.linalg', 'norm')
        model.set_name('1d_norm')
        model.set_title('Norm of a 1D Array')
        model.set_inputs('ndarray', 'Array to be normed', shape=[None])
        model.set_outputs('number', 'Norm of the array')

        # Submit the model
        self.dl.publish_servable(model)

    def test_describe_model(self):
        # Find the 1d_norm function from the test user (should be there)
        description = self.dl.describe_servable('dlhub.test_gmail', '1d_norm')
        self.assertEqual('dlhub.test_gmail', description['dlhub']['owner'])
        self.assertEqual('1d_norm', description['dlhub']['name'])

        # Give it a bogus name, check the error
        with self.assertRaises(AttributeError) as exc:
            self.dl.describe_servable('dlhub.test_gmail', 'nonexistant')
        self.assertIn('No such model', str(exc.exception))

        # Get only the method details
        expected = dict(description['servable']['methods'])
        del expected['run']['method_details']
        methods = self.dl.describe_methods('dlhub.test_gmail', '1d_norm')
        self.assertEqual(expected, methods)

        method = self.dl.describe_methods('dlhub.test_gmail', '1d_norm', 'run')
        self.assertEqual(expected['run'], method)
