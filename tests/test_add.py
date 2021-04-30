import unittest
from jit import jit, j_types as j, errors as err


@jit
def add(a, b):
    return a + b


@jit
def add0(a: j.i64, b: j.i64):
    return a + b

@jit
def add1(a: int):
    return a + 1


@jit
def add2(a: float):
    return a + 1.0


@jit
def add3(a: int, b: int):
    return a + b


@jit
def add4(a: float, b: float):
    return a + b


class Test(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add1(1), 2)
        self.assertEqual(add2(1.0), 2.0)
        self.assertEqual(add3(1, 1), 2)
        self.assertEqual(add4(1.0, 1.0), 2.0)    

    def test_add_err(self):
        with self.assertRaises(err.JitTypeError):
            add(2, 2.0)
            add0(2.0, 2.0)
