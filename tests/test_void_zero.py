import unittest
from jit import jit


@jit
def void():
    return


@jit
def zero():
    return 0


class Test(unittest.TestCase):
    def test_void_zero(self):
        self.assertEqual(void(), None)
        self.assertEqual(zero(), 0)
