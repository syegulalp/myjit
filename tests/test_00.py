import unittest
from jit import jit


@jit
def eq1():
    x=1
    return x==1

@jit
def eq2():
    x=1
    return x==2


class Test(unittest.TestCase):
    def test_return_constant(self):
        self.assertEqual(eq1(), True)
        self.assertEqual(eq2(), False)
