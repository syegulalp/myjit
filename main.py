from jit import jit

@jit
def main():
    x=1
    return x % 4

print (main())