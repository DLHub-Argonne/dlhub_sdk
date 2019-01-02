import unittest

import numpy as np

from dlhub_sdk.utils.types import simplify_numpy_dtype, compose_argument_block


class TestTypes(unittest.TestCase):

    def test_simplify(self):
        self.assertEqual(simplify_numpy_dtype(np.dtype('bool')), 'boolean')
        self.assertEqual(simplify_numpy_dtype(np.dtype('int32')), 'integer')
        self.assertEqual(simplify_numpy_dtype(np.dtype('double')), 'float')
        self.assertEqual(simplify_numpy_dtype(np.dtype('complex')), 'complex')
        date = np.datetime64('2005-02-25')
        self.assertEqual(simplify_numpy_dtype(date.dtype), 'datetime')
        self.assertEqual(simplify_numpy_dtype((date - date).dtype), 'timedelta')
        self.assertEqual(simplify_numpy_dtype(np.dtype('str')), 'string')
        self.assertEqual(simplify_numpy_dtype(np.dtype('object')), 'python object')

    def test_compose(self):
        self.assertEquals({'type': 'string', 'description': 'Test'},
                          compose_argument_block('string', 'Test'))

        # Test ndarray
        with self.assertRaises(ValueError):
            compose_argument_block("ndarray", 'Test')
        self.assertEquals({'type': 'ndarray', 'description': 'Test', 'shape': [2, 2]},
                          compose_argument_block('ndarray', 'Test', shape=[2, 2]))

        # Test Python object
        with self.assertRaises(ValueError):
            compose_argument_block('python object', 'Test')
        self.assertEquals({'type': 'python object', 'description': 'Test', 'python_type': 'fk.Cls'},
                          compose_argument_block('python object', 'Test', python_type='fk.Cls'))

        # Test list object
        with self.assertRaises(ValueError):
            compose_argument_block('list', 'Test')
        self.assertEquals({'type': 'list', 'description': 'Test', 'item_type': {'type': 'string'}},
                          compose_argument_block('list', 'Test', item_type='string'))

        # Test tuple object
        with self.assertRaises(ValueError):
            compose_argument_block('tuple', 'Test')
        self.assertEquals({'type': 'tuple', 'description': 'Test', 'element_types':
            [{'type': 'string', 'description': 'Item 1'},
             {'type': 'string', 'description': 'Item 2'}]},
                          compose_argument_block('tuple', 'Test', element_types=[
                                                 compose_argument_block('string', 'Item 1'),
                                                 compose_argument_block('string', 'Item 2')]))

        # Test Python object
        with self.assertRaises(ValueError):
            compose_argument_block('dict', 'Test')
        self.assertEquals({'type': 'dict', 'description': 'Test',
                           'properties': {'test': {'type': 'string', 'description': 'A string'}}},
                          compose_argument_block('dict', 'Test',
                                                 properties={'test': compose_argument_block('string', 'A string')}))
