from jit import jit

@jit
def main():
    x=1
    return x != 1

print (main())