from llvmlite import ir, binding
import sys
import ast, inspect, builtins
import pprint
import pathlib

from llvmlite.ir.types import VoidType
from .j_types import *
from .errors import JitTypeError, BaseJitError
from collections import namedtuple
from . import settings
from . import stdlib

from typing import Union


class JitObj:
    def __init__(self, j_type, llvm, obj):
        self.j_type = j_type
        self.llvm = llvm
        self.obj = obj

    def reify_type(self, other):
        pass


class Value(JitObj):
    pass


class Variable(JitObj):
    pass


class TypeTarget:
    def __init__(self, tt_list, type_target):
        self.tt_list = tt_list
        self.tt_list.append(type_target)

    def __enter__(self):
        pass

    def __exit__(self, *a):
        self.tt_list.pop()


class Codegen:
    def __init__(self):
        self.modules = {}
        self.target_data = None

    def val(self, obj: JitObj):
        if isinstance(obj, Value):
            return obj.llvm
        elif isinstance(obj, Variable):
            return self.builder.load(obj.llvm)

    def _coerce_bool(self, expression, node):
        if node.j_type != u1:
            expression = node.j_type.to_bool(self, expression)
        return expression

    def generate_function_name(self, name):
        return f"jit.{name}"

    def codegen_all(self, code_obj):

        # String name of the module this function lives in
        self.py_module_name: str = code_obj.__module__
        # Reference to module object that hosts function
        self.py_module = sys.modules.get(self.py_module_name)
        self.module: ir.Module = self.modules.get(self.py_module_name)

        if not self.module:
            self.module = ir.Module(self.py_module_name)
            self.modules[self.py_module_name] = self.module

        if not self.target_data:
            self.target_data = binding.create_target_data(self.module.data_layout)
            self.bitness = (
                ir.PointerType(ir.IntType(8)).get_abi_size(self.target_data) * 8
            )
            self.mem = ir.IntType(self.bitness)
            self.mem_ptr = ir.PointerType(self.mem)
            self.memv = lambda val: ir.Constant(ir.IntType(self.bitness), val)
            self.zero = self.memv(0)

        self.code_obj = code_obj
        self.instructions = ast.parse(inspect.getsource(code_obj))
        self.var_counter = 0

        dump_file = "debug"

        if settings.DUMP_TO_DIR:
            module_file = codegen.py_module.__file__
            module_path = pathlib.Path(module_file)
            dump_file = f"{module_path}.debug"

        if settings.DEBUG:
            with open(f"{dump_file}.debug.txt", "w") as self.output:
                self.codegen(self.instructions)

        if settings.DUMP:
            with open(f"{dump_file}.debug.llvm", "w") as self.output:
                self.output.write(str(self.module))

    def codegen(self, instruction):
        # print(instruction)
        itype = instruction.__class__.__name__
        self.output.write(f"\n\n>> {itype}\n\n")
        self.output.write(pprint.pformat(instruction.__dict__))
        call = getattr(self, f"visit_{itype}", None)
        if not call:
            print(itype)
            return
        try:
            return call(instruction)
        except BaseJitError as e:
            raise e

    def visit_Module(self, node: ast.Module):
        for module_node in node.body:
            self.codegen(module_node)

    def type_target(self, tt):
        return TypeTarget(self.type_targets, tt)

    def get_annotation(self, annotation):
        item = ast.unparse(annotation)
        arg_type = eval(item, self.py_module.__dict__)
        if not arg_type:
            raise JitTypeError("annotation not found")

        if not isinstance(arg_type, PrimitiveType):
            converted_arg_type = type_conversions(arg_type)

            if converted_arg_type is None:
                raise JitTypeError(f"Type {arg_type} not supported")
            arg_type = converted_arg_type

        if isinstance(arg_type, ObjectType):
            arg_type = objectpointer(arg_type)

        return arg_type

    def visit_ClassDef(self, node: ast.ClassDef):
        print(node.__dict__)

    def visit_FunctionDef(self, node: ast.FunctionDef):

        self.type_targets = []
        self.break_stack = []
        self.loop_stack = []
        self.argtypes = []

        for argument in node.args.args:
            if not argument.annotation:
                raise JitTypeError(f"Arg {argument.arg} not annotated")

            arg_type = self.get_annotation(argument.annotation)
            self.argtypes.append(arg_type)

        self.type_data: dict = {}
        self.type_unset: bool = False

        # set return type from annotation if available

        self.return_type: PrimitiveType = self.type_data.get("return", None)
        if not self.return_type:
            self.type_unset = True
            self.return_type = void

        function_returntype = (
            ir.VoidType() if self.return_type is void else self.return_type
        )
        self.functiontype = ir.FunctionType(
            function_returntype, [x.llvm for x in self.argtypes], False
        )
        self.function = ir.Function(self.module, self.functiontype, node.name)
        self.function.return_jtype = self.return_type
        self.builder = ir.IRBuilder()

        self.setup_block = self.function.append_basic_block("setup")
        self.entry_block = self.function.append_basic_block("entry")
        self.exit_block = self.function.append_basic_block("exit")

        self.builder = ir.IRBuilder(self.setup_block)
        # TODO: use type alloca

        if self.return_type is not void:
            self.return_value = Variable(
                self.return_type, self.return_type.alloca(self), None
            )
        else:
            self.return_value = void

        self.vars = {}

        for func_argument, argument, argtype in zip(
            self.function.args, node.args.args, self.argtypes
        ):
            # if isinstance(argtype, ObjectPointer):
            #     val = Value(argtype.pointee, self.builder.load(func_argument), argument)
            # else:
            val = Value(argtype, func_argument, argument)
            self.vars[argument.arg] = val

        self.setup_exit = self.builder.branch(self.entry_block)
        self.builder.position_at_start(self.entry_block)

        for instruction in node.body:
            self.codegen(instruction)

        if not self.builder._block.is_terminated:
            self.builder.branch(self.exit_block)

        self.builder.position_at_start(self.exit_block)

        if self.return_value is void:
            self.builder.ret_void()
        else:
            self.builder.ret(self.val(self.return_value))

    def visit_Return(self, node: ast.Return):
        if node.value is None:
            return

        return_value: JitObj = self.codegen(node.value)
        if return_value is None:
            return

        llvm = self.val(return_value)

        if return_value.j_type != self.return_type:
            if not self.type_unset:
                raise JitTypeError("too many return type redefinitions")
            self.return_type = return_value.j_type
            self.functiontype = ir.FunctionType(
                llvm.type, [x.llvm for x in self.argtypes], False
            )
            self.function.type = ir.PointerType(self.functiontype)
            self.function.ftype = self.functiontype
            self.function.return_value.type = llvm.type
            self.function.return_jtype = return_value.j_type
            self.type_unset = False

            with self.builder.goto_block(self.entry_block):
                self.builder.position_before(self.setup_exit)
                self.return_value = Variable(
                    self.return_type, self.return_type.alloca(self), None
                )

        self.builder.store(llvm, self.return_value.llvm)
        self.builder.branch(self.exit_block)

    def visit_Constant(self, node: ast.Constant):

        val = node.value
        default_type_to_use = type_conversions(val.__class__)

        if not default_type_to_use:
            raise JitTypeError("type not supported", type(node.value))

        if self.type_targets and self.type_targets[0] is not None:
            if not isinstance(self.type_targets[0], PrimitiveType):
                raise JitTypeError(
                    "can't coerce", type(node.value), self.type_targets[0]
                )
            default_type_to_use = self.type_targets[0]

        result = Value(
            default_type_to_use, ir.Constant(default_type_to_use.llvm, val), node
        )

        return result

    def visit_Name(self, node: ast.Name):

        var_ref = self.vars.get(node.id)
        if var_ref:
            # if isinstance(var_ref, ObjectPointer):
            #     return self.builder.load(var_ref)
            return var_ref

        var_ref = self.py_module.__dict__.get(node.id)

        # attempt to capture value at compile time from surrounding module
        # TODO: pass silently as a variable?

        if var_ref:
            new_node = ast.Constant(value=var_ref)
            new_value = self.codegen(new_node)
            self.create_name(node, new_value)
            return new_value

        return None

    def create_name(self, varname, value):
        with self.builder.goto_block(self.setup_block):
            alloc = value.j_type.alloca(self)
        ref = Variable(value.j_type, alloc, varname)
        self.vars[varname.id] = ref
        return ref

    def visit_Assign(self, node: Union[ast.Assign, ast.AnnAssign]):

        # TODO: allow multiple assign

        if isinstance(node, ast.AnnAssign):
            varname: ast.Name = node.target
        else:
            varname: ast.Name = node.targets[0]

        var_ref: JitObj = self.codegen(varname)

        if isinstance(node, ast.AnnAssign):
            tt = self.get_annotation(node.annotation)
        else:
            if var_ref is None:
                tt = None
            else:
                tt = var_ref.j_type

        with self.type_target(tt):
            value: JitObj = self.codegen(node.value)

        if not var_ref:
            ref = self.create_name(varname, value)
        else:
            ref = var_ref

        if isinstance(ref.j_type, PointerType):
            if ref.j_type.pointee != value.j_type:
                raise JitTypeError(
                    "mismatched types:", ref.j_type.pointee, value.j_type
                )
        elif ref.j_type != value.j_type:
            raise JitTypeError("mismatched types:", ref.j_type, value.j_type)

        ref_llvm = ref.llvm
        val = self.val(value)
        return self.builder.store(val, ref_llvm)

    def visit_AugAssign(self, node: ast.AugAssign):
        binop = ast.BinOp(left=node.target, right=node.value, op=node.op)
        assignment = ast.Assign(targets=[node.target], value=binop)
        return self.codegen(assignment)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        self.visit_Assign(node)

    def visit_BinOp(self, node: ast.BinOp):
        lhs: JitObj = self.codegen(node.left)
        # lhs_v = self.val_node(lhs)

        with self.type_target(lhs.j_type):
            rhs: JitObj = self.codegen(node.right)

        optype = node.op.__class__.__name__
        op = getattr(lhs.j_type, f"impl_{optype}", None)
        if not op:
            raise Exception("Op not supported", optype)

        if lhs.j_type != rhs.j_type:
            raise JitTypeError("mismatched types for op:", lhs.j_type, rhs.j_type)

        lhs_v = self.val(lhs)
        rhs_v = self.val(rhs)
        result = op(self, lhs_v, rhs_v)

        return Value(lhs.j_type, result, node)

    def visit_UnaryOp(self, node: ast.UnaryOp):

        lhs: JitObj = self.codegen(node.operand)

        optype = node.op.__class__.__name__
        op = getattr(lhs.j_type, f"impl_{optype}", None)
        if not op:
            raise Exception("Op not supported", optype)

        result = op(self, lhs)
        return Value(lhs.j_type, result, node)

    def visit_Compare(self, node: ast.Compare):

        # TODO: multi-comparison
        # maybe unpack that to if x==y and y==z

        lhs: JitObj = self.codegen(node.left)
        lhs_val = self.val(lhs)
        # lhs_n = self.val_node(lhs)
        # print(lhs_n.__dict__)

        with self.type_target(lhs.j_type):
            rhs: JitObj = self.codegen(node.comparators[0])
        rhs_val = self.val(rhs)

        optype = node.ops[0].__class__.__name__
        op = getattr(lhs.j_type, f"impl_{optype}", None)
        if not op:
            raise Exception("Op not supported", optype, lhs.j_type)

        if lhs.j_type != rhs.j_type:
            raise JitTypeError("mismatched types for op:", lhs.j_type, rhs.j_type)

        result = op(self, lhs_val, rhs_val)
        return Value(u1, result, node)

    def visit_If(self, node: ast.If):
        then_block = self.builder.append_basic_block("then")
        else_block = self.builder.append_basic_block("else")
        end_block = self.builder.append_basic_block("end")

        test_clause = self.codegen(node.test)
        test_clause_llvm = self._coerce_bool(self.val(test_clause), test_clause)

        self.builder.cbranch(test_clause_llvm, then_block, else_block)

        self.builder.position_at_start(then_block)
        for n in node.body:
            self.codegen(n)
        if not self.builder.block.is_terminated:
            self.builder.branch(end_block)

        self.builder.position_at_start(else_block)
        for n in node.orelse:
            self.codegen(n)
        if not self.builder.block.is_terminated:
            self.builder.branch(end_block)
        self.builder.position_at_start(end_block)

    def visit_While(self, node: ast.While):
        loop_block = self.builder.append_basic_block("while")
        end_block = self.builder.append_basic_block("end_while")
        self.loop_stack.append(loop_block)
        self.break_stack.append(end_block)

        self.builder.branch(loop_block)
        self.builder.position_at_start(loop_block)
        for n in node.body:
            self.codegen(n)
        test_clause = self.codegen(node.test)
        test_clause_llvm = self._coerce_bool(self.val(test_clause), test_clause)

        self.builder.cbranch(test_clause_llvm, loop_block, end_block)
        self.builder.position_at_start(end_block)

    def visit_Break(self, node: ast.Break):
        if not self.break_stack:
            raise Exception("break encountered outside of loop")
        break_target = self.break_stack.pop()
        self.builder.branch(break_target)

    def visit_Continue(self, node: ast.Continue):
        loop_target = self.loop_stack.pop()
        self.builder.branch(loop_target)

    def visit_Subscript(self, node: ast.Subscript):
        value = self.codegen(node.value)
        val_llvm = value.llvm

        slice = self.codegen(node.slice)
        index = self.val(slice)
        ptr = self.builder.gep(val_llvm, [self.zero, index])

        # TODO: this feels wrong
        # we should have a method for j-type that extracts
        # the j_type of a subscript

        if isinstance(value.j_type, ObjectPointer):
            return Value(value.j_type.pointee.base_type, ptr, None)

        return Variable(value.j_type.base_type, ptr, None)

    def visit_BoolOp(self, node: ast.BoolOp):

        # TODO: multicomparisons

        lhs = self.codegen(node.values[0])
        rhs = self.codegen(node.values[1])

        lhs_val = self.val(lhs)
        rhs_val = self.val(rhs)

        if isinstance(node.op, ast.And):
            result = self.builder.and_(lhs_val, rhs_val)

        return Value(u1, result, None)

    def visit_Expr(self, node: ast.Expr):
        return self.codegen(node.value)

    def visit_Call(self, node: ast.Call):

        # only one argument supported so far
        args = [self.codegen(_) for _ in node.args]
        # a_val = self.val(arg)
        vals = [self.val(_) for _ in args]

        function_name = node.func.id

        # TODO: will val pass a pointer to an object? find out

        # first, find out if this is a function that already exists
        # call = self.module.globals.get(function_name, None)
        # if call:
        #     return self.builder.call(call, vals)

        # next, find out if this is a function from the standard library
        call = stdlib.make(function_name)
        if call:
            return call(self, vals)

        raise Exception(f"no such function {function_name}")


codegen = Codegen()
