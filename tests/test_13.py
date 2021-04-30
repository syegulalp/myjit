import unittest
from jit import jit, j_types as j, errors as err

# type definition
arr = j.array(j.u8, (2, 80, 25))
# instance
x = arr()

x[0][0][0] = 5
x[1][79][24] = 32

# array is automatically passed by reference
@jit
def main(a: arr):
    a[0][0][0] = 100
    return a


@jit
def main2(a: arr):
    a[1][79][24] = 32


@jit
def main3(a: arr):
    xx1 = -1 % 80
    if a[1][xx1][24] > 0:
        return 1
    return 0

@jit
def main4(a: arr):
    xx = 1
    a[1][79][24] = xx


class Test(unittest.TestCase):
    def test_array(self):
        y = main(x)
        self.assertEqual(y[0][0][0], 100)
        self.assertEqual(y[0][0][1], 0)
        self.assertEqual(y[1][79][24], 32)

    def test_array2(self):
        x[0][0][0] = 5
        x[1][79][24] = 32
        main(x)
        self.assertEqual(x[0][0][0], 100)
        self.assertEqual(x[0][0][1], 0)
        self.assertEqual(x[1][79][24], 32)

    def test_array3(self):
        x[0][0][0] = 5
        # x[1][79][24] = 32
        main2(x)
        self.assertEqual(x[0][0][0], 5)
        self.assertEqual(x[0][0][1], 0)
        self.assertEqual(x[1][79][24], 32)

    def test_array4(self):
        x[1][79][24] = 0
        self.assertEqual(main3(x), False)
        x[1][79][24] = 1
        self.assertEqual(main3(x), True)
        with self.assertRaises(err.JitTypeError):
            main4()
