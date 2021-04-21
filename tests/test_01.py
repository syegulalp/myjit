import unittest
from jit import jit, j_types as j


@jit
def add1(a, b):
    return a + b


@jit
def add2(a: j.i64, b: j.i64):
    return a + b


class Test(unittest.TestCase):
    def test_return_constant(self):
        with self.assertRaises(TypeError):
            add1(2, 2.0)
            add2(2.0, 2.0)
