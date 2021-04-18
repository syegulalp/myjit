from .engine import jitengine


def jit(func):
    from .codegen import codegen as c

    c.codegen_all(func)
    f = jitengine.compile(c, entry_point=func.__name__)

    def wrapper(*a, **ka):
        return f()

    return wrapper
