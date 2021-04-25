from .engine import jitengine
from .codegen import codegen as c
from .j_types import JitType, ObjectType


def jit_m(name=None):
    def fn(func):
        func._new_name = name
        return jit(func)

    return fn


def jit(func):
    def wrapper(*a, **ka):
        aa = []
        for arg in a:
            if isinstance(arg, JitType):
                aa.append(arg.from_jtype(arg))
            else:
                aa.append(arg)
        try:
            return func._jit(*aa, **ka)
        except AttributeError:
            pass
        try:
            c.codegen_all(func)
        except Exception as e:
            raise e
        c1 = jitengine.compile(c, entry_point=func.__name__)
        func._jit = c1
        result = c1(*aa, **ka)
        if hasattr(result, "contents"):
            return result.contents
        return result

    wrapper.f = func

    return wrapper
