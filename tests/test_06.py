import unittest
from jit import jit


@jit
def void():
    return

@jit
def zero():
    return 0


class Test(unittest.TestCase):
    def test_return_constant(self):
        self.assertEqual(void(), None)
        self.assertEqual(zero(), 0)
