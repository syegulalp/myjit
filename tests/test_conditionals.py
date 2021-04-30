import unittest
from jit import jit


@jit
def cond1():
    x = 0
    while x < 10:
        x = x + 1
        if x == 5:
            break
    return x


@jit
def cond2():
    x = 0
    while x < 10:
        x = x + 1
    return x


@jit
def cond3():
    x = 0
    y = 0
    if x == 0:
        y = 1
    elif x > 0:
        y = 2
    else:
        y = 3
    return y


@jit
def cond4():
    x = 5
    y = 0
    if x == 0:
        y = 1
    elif x > 0:
        y = 2
    else:
        y = 3
    return y


@jit
def cond5():
    x = -1
    y = 0
    if x == 0:
        y = 1
    elif x > 0:
        y = 2
    else:
        y = 3
    return y


class Test(unittest.TestCase):
    def test_conditionals(self):
        self.assertEqual(cond1(), 5)
        self.assertEqual(cond2(), 10)
        self.assertEqual(cond3(), 1)
        self.assertEqual(cond4(), 2)
        self.assertEqual(cond5(), 3)
