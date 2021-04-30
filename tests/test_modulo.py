import unittest
from jit import jit


@jit
def mod1():
    x = 4
    return x % 4


@jit
def mod2():
    x = 0
    return x % 4


@jit
def mod3():
    x = 1
    return x % 4


@jit
def mod4():
    x = 2
    return x % 4


@jit
def mod5():
    x = -1
    return x % 4


@jit
def mod6():
    x = 7
    return x % 4


class Test(unittest.TestCase):
    def test_modulo(self):
        self.assertEqual(mod1(), 0)
        self.assertEqual(mod2(), 0)
        self.assertEqual(mod3(), 1)
        self.assertEqual(mod4(), 2)
        self.assertEqual(mod5(), 3)
        self.assertEqual(mod6(), 3)
