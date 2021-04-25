from jit import jit, j_types as j

arr = j.array(j.u8, [2, 80, 25])
x = arr()

x[0][0][0] = 5
x[1][79][24] = 32

# array is automatically passed by reference


@jit
def main(a: arr):
    a[0][0][0] = 100
    return a


y = main(x)
print(y[0][0][0])  # 100 instead of 5
print(y[1][79][24])  # still 32
