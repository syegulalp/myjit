import unittest
from jit import jit


@jit
def andtest():
    x = 1
    y = 2
    if x == 1 and y == 2:
        return 1


class Test(unittest.TestCase):
    def test_and(self):
        self.assertEqual(andtest(), True)
