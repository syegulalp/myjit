from jit import jit, j_types as j


@jit
def main(a: j.f64):
    return a + 2


print(main(1))
