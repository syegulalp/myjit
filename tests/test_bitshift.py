import unittest
from jit import jit


@jit
def sh1():
    x = 2
    return x << 2


@jit
def sh2():
    x = 8
    return x >> 2


class Test(unittest.TestCase):
    def test_bitshift(self):
        self.assertEqual(sh1(), 8)
        self.assertEqual(sh2(), 2)
