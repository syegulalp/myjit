from .engine import jitengine
from .codegen import codegen as c
from .j_types import JitType, ObjectType


def jit_m(name=None):
    def fn(func):
        func._new_name = name
        return jit(func)

    return fn


def jit(func):

    try:
        c.codegen_all(func)
    except Exception as e:
        raise e

    # TODO: separate compilation from extraction of function

    jitted_function = jitengine.compile(c, entry_point=func.__name__)
    func._jit = jitted_function

    def wrapper(*a, **ka):
        aa = []
        for arg in a:
            if isinstance(arg, JitType):
                aa.append(arg.from_jtype(arg))
            else:
                aa.append(arg)

        result = jitted_function(*aa, **ka)
        if hasattr(result, "contents"):
            return result.contents
        return result

    #wrapper.f = func
    wrapper._wrapped = func
    wrapper._jit = jitted_function

    return wrapper


def jit_lazy(func):
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

        # TODO: separate compilation from extraction of function

        jitted_function = jitengine.compile(c, entry_point=func.__name__)
        func._jit = jitted_function
        result = jitted_function(*aa, **ka)
        if hasattr(result, "contents"):
            return result.contents
        return result

    wrapper._wrapped = func
    # wrapper._jit = func._jit

    return wrapper
