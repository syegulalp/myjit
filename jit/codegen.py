from llvmlite import ir
import sys
import ast, inspect, builtins
import pprint

from llvmlite.ir.types import VoidType
from .j_types import *
from collections import namedtuple

from typing import Union


class JitObj:
    def __init__(self, j_type, llvm, obj):
        self.j_type = j_type
        self.llvm = llvm
        self.obj = obj

    def reify_type(self, other):
        pass


class AttrLookup:
    pass
    # Get an Attribute object and a namespace, and attempt to
    # return the object it points to


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

    def val(self, obj: JitObj):
        llvm = obj.llvm
        if isinstance(llvm, ir.AllocaInstr):
            llvm = self.builder.load(llvm)
        return llvm

    def codegen_all(self, code_obj):

        # String name of the module this function lives in
        self.py_module_name: str = code_obj.__module__
        # Reference to module object that hosts function
        self.py_module = sys.modules.get(self.py_module_name)

        self.module: ir.Module = self.modules.get(self.py_module_name)
        if not self.module:
            self.module = ir.Module(self.py_module_name)
            self.modules[self.py_module_name] = self.module

        self.code_obj = code_obj
        self.instructions = ast.parse(inspect.getsource(code_obj))
        self.var_counter = 0

        with open("debug.txt", "w") as self.output:
            self.codegen(self.instructions)

        with open("debug.llvm", "w") as self.output:
            self.output.write(str(self.module))

    def codegen(self, instruction):
        itype = instruction.__class__.__name__
        self.output.write(f"\n\n>> {itype}\n\n")
        self.output.write(pprint.pformat(instruction.__dict__))
        call = getattr(self, f"visit_{itype}", None)
        if not call:
            print(itype)
            return
        try:
            return call(instruction)
        except Exception as e:
            raise e

    def visit_Module(self, node: ast.Module):
        for module_node in node.body:
            self.codegen(module_node)

    def type_target(self, tt):
        return TypeTarget(self.type_targets, tt)

    def visit_FunctionDef(self, node: ast.FunctionDef):

        self.type_targets = []
        self.break_stack = []
        self.argtypes = []

        for argument in node.args.args:
            converted_arg_type = None
            if not argument.annotation:
                raise TypeError(f"Arg {argument.arg} not annotated")

            item = ast.unparse(argument.annotation)
            arg_type = eval(item, self.py_module.__dict__)

            if not arg_type:
                raise TypeError("annotation not found")

            if not isinstance(arg_type, PrimitiveType):
                converted_arg_type = type_conversions(arg_type)

                if converted_arg_type is None:
                    raise TypeError(f"Type {arg_type} not supported")
                arg_type = converted_arg_type

            if isinstance(arg_type, ObjectType):
                arg_type = pointer(arg_type)
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
            self.return_value = JitObj(
                self.return_type, self.return_type.alloca(self), None
            )
        else:
            self.return_value = void

        self.vars = {}

        for func_argument, argument, argtype in zip(
            self.function.args, node.args.args, self.argtypes
        ):
            # TODO: clumsy
            # if isinstance(argtype, ObjectType) or isinstance(getattr(argtype,'pointee'), ObjectType):
            #     unpack = self.builder.load(func_argument)
            #     self.vars[argument.arg] = JitObj(argtype.pointee, unpack, argument)
            # else:
            self.vars[argument.arg] = JitObj(argtype, func_argument, argument)

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
                raise Exception("too many return type redefinitions")
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
                self.return_value = JitObj(
                    self.return_type, self.return_type.alloca(self), None
                )

        self.builder.store(llvm, self.return_value.llvm)
        self.builder.branch(self.exit_block)

    def visit_Constant(self, node: ast.Constant):
        val = node.value
        default_type_to_use = type_conversions(val.__class__)
        if not default_type_to_use:
            raise Exception("type not supported", type(node.value))
        if self.type_targets and self.type_targets[0] is not None:
            default_type_to_use = self.type_targets[0]
        result = JitObj(
            default_type_to_use, ir.Constant(default_type_to_use.llvm, val), node
        )

        return result

    def visit_Name(self, node: ast.Name):
        var_ref = self.vars.get(node.id)
        if not var_ref:
            return None
            #raise Exception("undefined var")
        return var_ref

    def visit_Assign(self, node: Union[ast.Assign, ast.AnnAssign]):
        # TODO: allow multiple assign
        if isinstance(node, ast.AnnAssign):
            varname: ast.Name = node.target
        else:
            varname: ast.Name = node.targets[0]

        # TODO: pointer check when recipient
        var_ref: JitObj = self.codegen(varname)

        if var_ref is None:
            tt = var_ref
        # TODO: ensure the pointer in question points to an actual variable
        # we need some way to know this
        elif isinstance(var_ref.j_type, PointerType):
            tt = var_ref.j_type.pointee
        else:
            tt = var_ref.j_type
        with self.type_target(tt):
            value: JitObj = self.codegen(node.value)
        
                
        #self.vars.get(varname.id)

        if not var_ref:
            alloc = value.j_type.alloca(self)
            # self.builder.alloca(value.j_type.llvm)
            ref = JitObj(value.j_type, alloc, varname)
            self.vars[varname.id] = ref
        else:
            ref = var_ref

        if isinstance(ref.j_type, PointerType):
            if ref.j_type.pointee != value.j_type:
                raise Exception("mismatched types:", ref.j_type.pointee, value.j_type)
        elif ref.j_type != value.j_type:
            raise Exception("mismatched types:", ref.j_type, value.j_type)

        ref_llvm = ref.llvm
        return self.builder.store(value.llvm, ref_llvm)

    def visit_AugAssign(self, node: ast.AugAssign):
        binop = ast.BinOp(left=node.target, right=node.value, op=node.op)
        assignment = ast.Assign(targets=[node.target], value=binop)
        return self.codegen(assignment)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        self.visit_Assign(node)

    def visit_BinOp(self, node: ast.BinOp):
        lhs: JitObj = self.codegen(node.left)

        with self.type_target(lhs.j_type):
            rhs: JitObj = self.codegen(node.right)

        optype = node.op.__class__.__name__
        op = getattr(lhs.j_type, f"impl_{optype}", None)
        if not op:
            raise Exception("Op not supported", optype)

        if lhs.j_type != rhs.j_type:
            raise Exception("mismatched types for op:", lhs.j_type, rhs.j_type)

        result = op(self, lhs, rhs)
        return JitObj(lhs.j_type, result, node)

    def visit_UnaryOp(self, node: ast.UnaryOp):

        lhs: JitObj = self.codegen(node.operand)

        optype = node.op.__class__.__name__
        op = getattr(lhs.j_type, f"impl_{optype}", None)
        if not op:
            raise Exception("Op not supported", optype)

        result = op(self, lhs)
        return JitObj(lhs.j_type, result, node)

    def visit_Compare(self, node: ast.Compare):

        # TODO: multi-comparison
        # maybe unpack that to if x==y and y==z

        lhs: JitObj = self.codegen(node.left)
        rhs: JitObj = self.codegen(node.comparators[0])

        optype = node.ops[0].__class__.__name__
        op = getattr(lhs.j_type, f"impl_{optype}", None)
        if not op:
            raise Exception("Op not supported", optype)

        if lhs.j_type != rhs.j_type:
            raise Exception("mismatched types for op:", lhs.j_type, rhs.j_type)

        result = op(self, lhs, rhs)
        return JitObj(u1, result, node)

    def visit_If(self, node: ast.If):
        then_block = self.builder.append_basic_block("then")
        else_block = self.builder.append_basic_block("else")
        end_block = self.builder.append_basic_block("end")

        test_clause = self.codegen(node.test)
        test_clause_llvm = self.val(test_clause)
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
        self.break_stack.append(end_block)

        self.builder.branch(loop_block)
        self.builder.position_at_start(loop_block)
        for n in node.body:
            self.codegen(n)
        test_clause = self.codegen(node.test)
        test_clause_llvm = self.val(test_clause)
        self.builder.cbranch(test_clause_llvm, loop_block, end_block)
        self.builder.position_at_start(end_block)

    def visit_Break(self, node: ast.Break):
        if not self.break_stack:
            raise Exception("break encountered outside of loop")
        break_target = self.break_stack.pop()
        self.builder.branch(break_target)

    def visit_Subscript(self, node: ast.Subscript):
        value = self.codegen(node.value)
        val_llvm = self.val(value)

        slice = self.codegen(node.slice)
        index = self.val(slice)

        ptr = self.builder.gep(val_llvm, [ir.Constant(u64.llvm, 0), index])
        return JitObj(pointer(value.j_type.pointee.base_type), ptr, None)


codegen = Codegen()
