import unittest
from jit import jit


@jit
def lt1():
    x = 1
    return x < 2


@jit
def lt2():
    x = 1
    return x < 0


@jit
def lt3():
    x = 1.0
    return x < 2.0


@jit
def lt4():
    x = 1.0
    return x < 0.0


@jit
def lt5():
    x = 2
    return x <= 2


@jit
def lt6():
    x = 1
    return x <= 0


@jit
def lt7():
    x = 1.0
    return x <= 2.0


@jit
def lt8():
    x = 1.0
    return x <= 0.0


class Test(unittest.TestCase):
    def test_return_constant(self):
        self.assertEqual(lt1(), True)
        self.assertEqual(lt2(), False)
        self.assertEqual(lt3(), True)
        self.assertEqual(lt4(), False)
        self.assertEqual(lt5(), True)
        self.assertEqual(lt6(), False)
        self.assertEqual(lt7(), True)
        self.assertEqual(lt8(), False)
