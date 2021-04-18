import ctypes
from llvmlite import ir


class JitType:
    llvm = None

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


class BaseInteger(PrimitiveType):

    j_type = ir.IntType

    _from_ctype = {
        True: {64: ctypes.c_int64},
        False: {64: ctypes.c_uint64, 1: ctypes.c_bool},
    }

    def to_ctype(self):
        return self._from_ctype[self.signed][self.size]

    def impl_BINARY_ADD(self, codegen, lhs, rhs):
        return codegen.builder.add(lhs, rhs)

    def impl_BINARY_SUBTRACT(self, codegen, lhs, rhs):
        return codegen.builder.sub(lhs, rhs)

    def impl_BINARY_MULTIPLY(self, codegen, lhs, rhs):
        return codegen.builder.mul(lhs, rhs)

    def impl_BINARY_LSHIFT(self, codegen, lhs, rhs):
        return codegen.builder.shl(lhs, rhs)


class SignedInteger(BaseInteger):
    signed = True

    def impl_BINARY_TRUE_DIVIDE(self, codegen, lhs, rhs):
        return codegen.builder.sdiv(lhs, rhs)

    def impl_UNARY_NEGATIVE(self, codegen, lhs):
        return codegen.builder.sub(ir.Constant(lhs.type, 0), lhs)

    def impl_BINARY_MODULO(self, codegen, lhs, rhs):
        return codegen.builder.srem(lhs, rhs)

    def impl_BINARY_RSHIFT(self, codegen, lhs, rhs):
        return codegen.builder.ashr(lhs, rhs)

    def impl_COMPARE_OP(self, codegen, lhs, rhs, op):
        return codegen.builder.icmp_signed(op, lhs, rhs)


class UnsignedInteger(BaseInteger):
    signed = False

    def impl_BINARY_TRUE_DIVIDE(self, codegen, lhs, rhs):
        return codegen.builder.udiv(lhs, rhs)

    def impl_UNARY_NEGATIVE(self, codegen, lhs):
        raise Exception("negation not allowed with unsigned type")

    def impl_BINARY_MODULO(self, codegen, lhs, rhs):
        return codegen.builder.urem(lhs, rhs)

    def impl_BINARY_RSHIFT(self, codegen, lhs, rhs):
        return codegen.builder.lshr(lhs, rhs)


class BaseFloat(PrimitiveType):
    signed = True

    def __init__(self):
        self.llvm = self.j_type()

    def impl_BINARY_ADD(self, codegen, lhs, rhs):
        return codegen.builder.fadd(lhs, rhs)

    def impl_BINARY_SUBTRACT(self, codegen, lhs, rhs):
        return codegen.builder.fsub(lhs, rhs)

    def impl_BINARY_MULTIPLY(self, codegen, lhs, rhs):
        return codegen.builder.fmul(lhs, rhs)

    def impl_BINARY_TRUE_DIVIDE(self, codegen, lhs, rhs):
        return codegen.builder.fdiv(lhs, rhs)

    def impl_BINARY_MODULO(self, codegen, lhs, rhs):
        return codegen.builder.frem(lhs, rhs)

    def impl_COMPARE_OP(self, codegen, lhs, rhs, op):
        return codegen.builder.fcmp_unordered(op, lhs, rhs)
        # unordered implies either operand could be a QNAN


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
