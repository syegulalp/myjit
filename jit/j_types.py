import ctypes
from llvmlite import ir


class JitType:
    llvm = None

    def alloca(self):
        raise NotImplementedError


class Void(JitType):
    llvm = ir.VoidType()
    signed = None

    def to_ctype(self):
        return lambda x: None


class PrimitiveType(JitType):
    signed = None

    def __init__(self, size):
        self.size = size
        self.llvm = self.j_type(self.size)

    def __repr__(self):
        return f'<{"Un" if not self.signed else ""}signed i{self.size}>'

    def alloca(self, codegen):
        return codegen.builder.alloca(self.llvm)


def _op(codegen, lhs, rhs):
    return codegen.val(lhs), codegen.val(rhs)


class BaseInteger(PrimitiveType):

    j_type = ir.IntType

    _from_ctype = {
        True: {
            64: ctypes.c_int64,
            32: ctypes.c_int32,
            16: ctypes.c_int16,
            8: ctypes.c_int8,
        },
        False: {
            64: ctypes.c_uint64,
            32: ctypes.c_uint32,
            16: ctypes.c_uint16,
            8: ctypes.c_uint8,
            1: ctypes.c_bool,
        },
    }

    def to_ctype(self):
        return self._from_ctype[self.signed][self.size]

    def impl_Add(self, codegen, lhs, rhs):
        lhs_l, rhs_l = _op(codegen, lhs, rhs)
        return codegen.builder.add(lhs_l, rhs_l)

    def impl_Sub(self, codegen, lhs, rhs):
        lhs_l, rhs_l = _op(codegen, lhs, rhs)
        return codegen.builder.sub(lhs_l, rhs_l)

    def impl_Mult(self, codegen, lhs, rhs):
        lhs_l, rhs_l = _op(codegen, lhs, rhs)
        return codegen.builder.mul(lhs_l, rhs_l)

    def impl_LShift(self, codegen, lhs, rhs):
        lhs_l, rhs_l = _op(codegen, lhs, rhs)
        return codegen.builder.shl(lhs_l, rhs_l)

    def impl_RShift(self, codegen, lhs, rhs):
        lhs_l, rhs_l = _op(codegen, lhs, rhs)
        return codegen.builder.ashr(lhs_l, rhs_l)


class SignedInteger(BaseInteger):
    signed = True

    def impl_Div(self, codegen, lhs, rhs):
        lhs_l, rhs_l = _op(codegen, lhs, rhs)
        return codegen.builder.sdiv(lhs_l, rhs_l)

    def impl_USub(self, codegen, lhs):
        lhs_l = codegen.val(lhs)
        return codegen.builder.sub(ir.Constant(lhs_l.type, 0), lhs_l)

    def impl_Mod(self, codegen, lhs, rhs):
        lhs_l, rhs_l = _op(codegen, lhs, rhs)
        return codegen.builder.srem(lhs_l, rhs_l)

    def impl_Eq(self, codegen, lhs, rhs):
        lhs_l, rhs_l = _op(codegen, lhs, rhs)
        return codegen.builder.icmp_signed("==", lhs_l, rhs_l)

    def impl_NotEq(self, codegen, lhs, rhs):
        lhs_l, rhs_l = _op(codegen, lhs, rhs)
        return codegen.builder.icmp_signed("!=", lhs_l, rhs_l)

    def impl_Gt(self, codegen, lhs, rhs):
        lhs_l, rhs_l = _op(codegen, lhs, rhs)
        return codegen.builder.icmp_signed(">", lhs_l, rhs_l)

    def impl_Lt(self, codegen, lhs, rhs):
        lhs_l, rhs_l = _op(codegen, lhs, rhs)
        return codegen.builder.icmp_signed("<", lhs_l, rhs_l)

    def impl_GtE(self, codegen, lhs, rhs):
        lhs_l, rhs_l = _op(codegen, lhs, rhs)
        return codegen.builder.icmp_signed(">=", lhs_l, rhs_l)

    def impl_LtE(self, codegen, lhs, rhs):
        lhs_l, rhs_l = _op(codegen, lhs, rhs)
        return codegen.builder.icmp_signed("<=", lhs_l, rhs_l)


class UnsignedInteger(BaseInteger):
    signed = False


class BaseFloat(PrimitiveType):
    signed = True

    def __repr__(self):
        return f'<{"Un" if not self.signed else ""}signed u{self.size}>'

    def __init__(self):
        self.llvm = self.j_type()

    def impl_Add(self, codegen, lhs, rhs):
        lhs_l, rhs_l = _op(codegen, lhs, rhs)
        return codegen.builder.fadd(lhs_l, rhs_l)

    def impl_Sub(self, codegen, lhs, rhs):
        lhs_l, rhs_l = _op(codegen, lhs, rhs)
        return codegen.builder.fsub(lhs_l, rhs_l)

    def impl_Mult(self, codegen, lhs, rhs):
        lhs_l, rhs_l = _op(codegen, lhs, rhs)
        return codegen.builder.fmul(lhs_l, rhs_l)

    def impl_Div(self, codegen, lhs, rhs):
        lhs_l, rhs_l = _op(codegen, lhs, rhs)
        return codegen.builder.fdiv(lhs_l, rhs_l)

    def impl_USub(self, codegen, lhs):
        lhs_l = codegen.val(lhs)
        return codegen.builder.fsub(ir.Constant(lhs_l.type, 0.0), lhs_l)

    def impl_Eq(self, codegen, lhs, rhs):
        lhs_l, rhs_l = _op(codegen, lhs, rhs)
        return codegen.builder.fcmp_unordered("==", lhs_l, rhs_l)

    def impl_NotEq(self, codegen, lhs, rhs):
        lhs_l, rhs_l = _op(codegen, lhs, rhs)
        return codegen.builder.fcmp_unordered("!=", lhs_l, rhs_l)

    def impl_Gt(self, codegen, lhs, rhs):
        lhs_l, rhs_l = _op(codegen, lhs, rhs)
        return codegen.builder.fcmp_unordered(">", lhs_l, rhs_l)

    def impl_Lt(self, codegen, lhs, rhs):
        lhs_l, rhs_l = _op(codegen, lhs, rhs)
        return codegen.builder.fcmp_unordered("<", lhs_l, rhs_l)

    def impl_GtE(self, codegen, lhs, rhs):
        lhs_l, rhs_l = _op(codegen, lhs, rhs)
        return codegen.builder.fcmp_unordered(">=", lhs_l, rhs_l)

    def impl_LtE(self, codegen, lhs, rhs):
        lhs_l, rhs_l = _op(codegen, lhs, rhs)
        return codegen.builder.fcmp_unordered("<=", lhs_l, rhs_l)


class Float(BaseFloat):
    size = 32

    def to_ctype(self):
        return ctypes.c_float

    j_type = ir.FloatType


class Double(BaseFloat):
    size = 64

    def to_ctype(self):
        return ctypes.c_double

    j_type = ir.DoubleType


i64 = SignedInteger(64)
u64 = UnsignedInteger(64)

i32 = SignedInteger(32)
u32 = UnsignedInteger(32)

i16 = SignedInteger(16)
u16 = UnsignedInteger(16)

i8 = SignedInteger(8)
ubyte = UnsignedInteger(8)
u8 = ubyte

u1 = UnsignedInteger(1)

f64 = Double()
f32 = Float()

void = Void()


class ArrayType(JitType):
    def __init__(self, base_type, dimensions):
        self.base_type = base_type.llvm
        self.dimensions = dimensions

        latest = self.base_type
        for n in reversed(self.dimensions):
            latest = ir.ArrayType(latest, n)
        self.llvm = latest


def array(base_type, dimensions):
    return ArrayType(base_type, dimensions)


type_conversions = {int: i64, float: f64}
