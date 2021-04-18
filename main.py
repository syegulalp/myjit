from jit import jit

@jit
def main():
    x=1
    return x*2

print (main())