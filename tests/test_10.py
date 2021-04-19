import unittest
from jit import jit


@jit
def add1(a:int):
    return a+1

@jit
def add2(a:float):
    return a+1.0

@jit
def add3(a:int, b:int):
    return a+b

@jit
def add4(a:float, b:float):
    return a+b

class Test(unittest.TestCase):
    def test_return_constant(self):
        self.assertEqual(add1(1),2)
        self.assertEqual(add2(1.0),2.0)
        self.assertEqual(add3(1,1),2)
        self.assertEqual(add4(1.0, 1.0),2.0)