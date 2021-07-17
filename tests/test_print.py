import unittest
from jit import jit
from jit import j_types as j


@jit
def test_print(x: j.i64):
    return print(x)


class Test(unittest.TestCase):
    def test_void_zero(self):
        self.assertEqual(test_print(8), 2)
        self.assertEqual(test_print(64), 3)
