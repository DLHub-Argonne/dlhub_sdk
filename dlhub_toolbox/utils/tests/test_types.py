import unittest

import numpy as np

from dlhub_toolbox.utils.types import simplify_numpy_dtype


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
        self.assertEqual(simplify_numpy_dtype(np.dtype('object')), 'object')
