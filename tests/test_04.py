import unittest
from jit import jit


@jit
def neg1():
    x = 2
    return -x


@jit
def neg2():
    x = 2.0
    return -x


class Test(unittest.TestCase):
    def test_return_constant(self):
        self.assertEqual(neg1(), -2)
        self.assertEqual(neg2(), -2.0)
