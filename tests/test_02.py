import unittest
from jit import jit


@jit
def mul1():
    x=2
    return x*2

@jit
def mul2():
    x=2.0
    return x*2.5


class Test(unittest.TestCase):
    def test_return_constant(self):
        self.assertEqual(mul1(), 4)
        self.assertEqual(mul2(), 5.0)
