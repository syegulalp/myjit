import unittest
from jit import jit, j_types as j
import ctypes


@jit
def inf1(a: j.f64):
    return a + 2


@jit
def inf2(a: j.i32):
    return a + 2


class Test(unittest.TestCase):
    def test_inference(self):

        self.assertEqual(inf1(2), 4.0)
        self.assertEqual(inf2(2), 4)

        self.assertEqual(inf1._jit.restype, ctypes.c_double)
        self.assertEqual(inf2._jit.restype, ctypes.c_int32)
