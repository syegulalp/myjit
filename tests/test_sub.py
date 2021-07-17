import unittest
from jit import jit


@jit
def sub1():
    x = 3
    return x - 1


@jit
def sub2():
    x = 3.0
    return x - 1.5


class Test(unittest.TestCase):
    def test_sub(self):
        self.assertEqual(sub1(), 2)
        self.assertEqual(sub2(), 1.5)
