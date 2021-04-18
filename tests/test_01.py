import unittest
from jit import jit


@jit
def add1():
    x=1
    return x+2

@jit
def add2():
    x=1.0
    return x+2.5

@jit
def sub1():
    x=3
    return x-1

@jit
def sub2():
    x=3.0
    return x-1.5

class Test(unittest.TestCase):
    def test_return_constant(self):
        self.assertEqual(add1(), 3)
        self.assertEqual(add2(), 3.5)
        self.assertEqual(sub1(), 2)
        self.assertEqual(sub2(), 1.5)
