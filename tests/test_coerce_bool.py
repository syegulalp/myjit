import unittest
from jit import jit


@jit
def coerce_from_int():
    x = 5
    if x:
        return 1
    else:
        return 0

@jit
def coerce_from_int2():
    x = 0
    if x:
        return 1
    else:
        return 0

@jit
def coerce_from_float():
    x = 1.0
    if x:
        return 1
    else:
        return 0

@jit
def coerce_from_float2():
    x = 0.0
    if x:
        return 1
    else:
        return 0        

class Test(unittest.TestCase):
    def test_void_zero(self):
        self.assertEqual(coerce_from_int(), True)
        self.assertEqual(coerce_from_int2(), False)
        self.assertEqual(coerce_from_float(), True)
        self.assertEqual(coerce_from_float2(), False)

