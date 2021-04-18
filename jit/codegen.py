from llvmlite import ir
import sys
import ast, inspect
import pprint

from llvmlite.ir.types import VoidType
from .j_types import *
from collections import namedtuple

JitObj = namedtuple("JitObj", "j_type, llvm, obj")


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

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.argtypes = []

        self.type_data: dict = {}

        self.type_unset: bool = False
        self.return_type: PrimitiveType = self.type_data.get("return", None)
        if not self.return_type:
            self.type_unset = True
            self.return_type = void

        function_returntype = (
            ir.VoidType() if self.return_type is void else self.return_type
        )
        self.functiontype = ir.FunctionType(function_returntype, [], False)
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
                self.return_type, self.builder.alloca(self.return_type.llvm), None
            )
        else:
            self.return_value = void

        self.builder.branch(self.entry_block)
        self.builder.position_at_start(self.entry_block)

        self.vars = {}

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

        return_value = self.codegen(node.value)
        llvm = self.val(return_value)

        if return_value.j_type != self.return_type:
            if not self.type_unset:
                raise Exception("return type redefinition")
            self.return_type = return_value.j_type
            self.functiontype = ir.FunctionType(llvm.type, [], False)
            self.function.type = ir.PointerType(self.functiontype)
            self.function.ftype = self.functiontype
            self.function.return_value.type = llvm.type
            self.function.return_jtype = return_value.j_type
            self.type_unset = False
            self.return_value = JitObj(
                self.return_type, self.builder.alloca(self.return_type.llvm), None
            )

        self.builder.store(llvm, self.return_value.llvm)
        self.builder.branch(self.exit_block)

    def visit_Constant(self, node: ast.Constant):
        val = node.value
        if isinstance(val, int):
            result = JitObj(i64, ir.Constant(i64.llvm, val), val)
        elif isinstance(val, float):
            result = JitObj(f64, ir.Constant(f64.llvm, val), val)
        return result

    def visit_Name(self, node: ast.Name):
        var_ref = self.vars.get(node.id)
        if not var_ref:
            raise Exception("undefined var")
        return var_ref

    def visit_Assign(self, node: ast.Assign):
        # TODO: allow multiple assign
        varname: ast.Name = node.targets[0]

        value = self.codegen(node.value)
        var_ref = self.vars.get(varname.id)
        if not var_ref:
            var_ref = self.builder.alloca(value.j_type.llvm)
            self.vars[varname.id] = JitObj(value.j_type, var_ref, varname)
            ref = var_ref
        else:
            ref = var_ref.llvm
        return self.builder.store(value.llvm, ref)

    def visit_BinOp(self, node: ast.BinOp):
        lhs = self.codegen(node.left)
        rhs = self.codegen(node.right)
        optype = node.op.__class__.__name__
        op = getattr(lhs.j_type, f"impl_{optype}", None)
        if not op:
            raise Exception("Op not supported", optype)
        result = op(self, lhs, rhs)
        return JitObj(lhs.j_type, result, node)

    def visit_UnaryOp(self, node: ast.UnaryOp):
        lhs = self.codegen(node.operand)
        optype = node.op.__class__.__name__
        op = getattr(lhs.j_type, f"impl_{optype}", None)
        if not op:
            raise Exception("Op not supported", optype)
        result = op(self, lhs)
        return JitObj(lhs.j_type, result, node)

    def visit_Compare(self, node: ast.Compare):
        # TODO: multi-comparison
        # maybe unpack that to if x==y and y==z
        lhs = self.codegen(node.left)
        rhs = self.codegen(node.comparators[0])
        optype = node.ops[0].__class__.__name__
        op = getattr(lhs.j_type, f"impl_{optype}", None)
        if not op:
            raise Exception("Op not supported", optype)
        result = op(self, lhs, rhs)
        return JitObj(u1, result, node)


codegen = Codegen()