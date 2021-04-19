from jit import jit, j_types as j

@jit
def main():
    x=0
    while x < 10:
        x = x + 1
        if x == 5:
            break
    return x


print(main())
