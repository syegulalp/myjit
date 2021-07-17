from llvmlite import ir


def make(function_name):

    maker = globals().get(f"make_{function_name}", None)
    if not maker:
        return None

    return maker


def _make_llvm(
    self, function_name, return_type=ir.VoidType, arguments=[], var_arg=False
):
    m: ir.Module = self.module

    p_func = m.globals.get("function_name", None)
    if p_func:
        return p_func

    p_func = ir.Function(
        self.module,
        ir.FunctionType(
            return_type,
            arguments,
            var_arg=var_arg,
        ),
        function_name,
    )
    return p_func


def make_print(self, args):

    from .codegen import Value
    from . import j_types as j

    p_func = _make_llvm(
        self,
        "printf",
        ir.IntType(64),
        [ir.PointerType(ir.IntType(8)), ir.IntType(64)],
        var_arg=True,
    )

    s1 = ir.GlobalVariable(self.module, ir.ArrayType(ir.IntType(8), 6), "str_1")

    s1.initializer = ir.Constant(
        ir.ArrayType(ir.IntType(8), 6), bytearray("%lld\n\x00", encoding="utf8")
    )

    s2 = self.builder.gep(s1, [self.zero, self.zero])

    result = self.builder.call(p_func, [s2] + args)
    return Value(j.u64, result, None)
