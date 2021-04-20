import unittest
from jit import jit


@jit
def gt1():
    x = 1
    return x > 0


@jit
def gt2():
    x = 1
    return x > 1


@jit
def gt3():
    x = 1.0
    return x > 0.0


@jit
def gt4():
    x = 1.0
    return x > 1.0


@jit
def gt5():
    x = 0
    return x >= 0


@jit
def gt6():
    x = -1
    return x >= 1


@jit
def gt7():
    x = 1.0
    return x >= 1.0


@jit
def gt8():
    x = 1.0
    return x >= 2.0


class Test(unittest.TestCase):
    def test_return_constant(self):
        self.assertEqual(gt1(), True)
        self.assertEqual(gt2(), False)
        self.assertEqual(gt3(), True)
        self.assertEqual(gt4(), False)
        self.assertEqual(gt5(), True)
        self.assertEqual(gt6(), False)
        self.assertEqual(gt7(), True)
        self.assertEqual(gt8(), False)
