import unittest
from jit import jit


@jit
def eq1():
    x = 1
    return x == 1


@jit
def eq2():
    x = 1
    return x == 2


@jit
def eq3():
    x = 1.0
    return x == 1.0


@jit
def eq4():
    x = 1.0
    return x == 2.0

@jit
def neq1():
    x = 1
    return x != 0


@jit
def neq2():
    x = 1
    return x != 1


@jit
def neq3():
    x = 1.0
    return x != 2.0


@jit
def neq4():
    x = 1.0
    return x != 1.0

class Test(unittest.TestCase):
    def test_return_constant(self):
        self.assertEqual(eq1(), True)
        self.assertEqual(eq2(), False)
        self.assertEqual(eq3(), True)
        self.assertEqual(eq4(), False)
        self.assertEqual(neq1(), True)
        self.assertEqual(neq2(), False)
        self.assertEqual(neq3(), True)
        self.assertEqual(neq4(), False)