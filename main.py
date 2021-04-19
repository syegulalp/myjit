from jit import jit, j_types as j


@jit
def main(a:int):
    return a+1


print(main(1))
