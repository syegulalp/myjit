from jit import jit, j_types as j
import array

arr = j.array(j.u8, [2,32])
x = arr()
x[0][0]=5
x[1][0]=32

@jit
def main(a: arr):
    a[0][0] = 100
    return a

y=main(x)
print(y[0][0])
print(y[1][0])

