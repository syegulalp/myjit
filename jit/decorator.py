from .engine import jitengine
from .codegen import codegen as c

def jit(func):
    
    def wrapper(*a, **ka):
        try:
            return func._jit()
        except AttributeError:
            pass
        try:
            c.codegen_all(func)
        except Exception as e:
            raise e
        c1 = jitengine.compile(c, entry_point=func.__name__)
        func._jit = c1
        return c1(*a, **ka)

    return wrapper
