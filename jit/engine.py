import llvmlite.binding as llvm
from ctypes import CFUNCTYPE, ArgumentError
from .j_types import PrimitiveType
import pathlib
from .errors import JitTypeError

from . import settings

class JitEngine:
    def __init__(self):
        llvm.initialize()
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()
        self.modules = {}
        self.engines = {}
        self.engine = None

    def create_execution_engine(self):
        # Create a target machine representing the host
        target = llvm.Target.from_default_triple()
        target_machine = target.create_target_machine()
        # And an execution engine with an empty backing module
        backing_mod = llvm.parse_assembly("")
        engine = llvm.create_mcjit_compiler(backing_mod, target_machine)

        self.pm = llvm.ModulePassManager()
        llvm.PassManagerBuilder().populate(self.pm)
        return engine

    def compile_ir(self, llvm_ir, opt_level=None):
        # Create a LLVM module object from the IR
        try:
            mod = llvm.parse_assembly(llvm_ir)
            if opt_level:
                if opt_level is True:
                    opt_level = 3
                self.pm.opt_level = opt_level
                self.pm.run(mod)
        except RuntimeError as e:
            print(llvm_ir)
            raise e
        mod.verify()

        # Now add the module and make sure it is ready for execution
        self.engine.add_module(mod)
        self.engine.finalize_object()
        self.engine.run_static_constructors()

        with open("debug.opt.llvm", "w") as f:
            f.write(str(mod))
        return mod

    def compile(self, codegen, opt_level=None, entry_point="main"):

        module_file = codegen.py_module.__file__
        module_path = pathlib.Path(module_file)
        module_base_path = module_path.parent
        module_filename = module_path.parts[-1]
        jit_module_filename = f"{module_filename}.jit"
        obj_module_filename = f"{module_filename}.obj"
        jit_module_path = pathlib.Path(module_base_path, jit_module_filename)

        self.engine = self.engines.get(codegen.py_module_name, None)
        if self.engine is None:
            self.engine = self.create_execution_engine()

            if settings.ASM:

                def obj_write(module, buffer):
                    with open(module_base_path / obj_module_filename, "wb") as f:
                        f.write(buffer)

                self.engine.set_object_cache(obj_write)

        do_jit = False

        function_name = codegen.code_obj.__name__
        if not self.engine.get_function_address(function_name):
            do_jit = True

        if jit_module_path.exists():
            if jit_module_path.stat().st_mtime < module_path.stat().st_mtime:
                do_jit = True
        else:
            do_jit = True

        if do_jit:
            mod = self.compile_ir(str(codegen.module), opt_level)
            if settings.CACHE:
                with open(f"{module_file}.jit", "wb") as f:
                    f.write(mod.as_bitcode())
        else:
            with open(f"{module_file}.jit", "rb") as f:
                bitcode = f.read()
            mod = llvm.parse_bitcode(bitcode)
            mod.verify()
            self.engine.add_module(mod)
            self.engine.finalize_object()
            self.engine.run_static_constructors()

        self.modules[codegen.py_module_name] = mod

        arg_types = [_.to_ctype() for _ in codegen.argtypes]
        func = codegen.module.globals[entry_point]
        cfunctype = CFUNCTYPE(func.return_jtype.to_ctype(), *arg_types)

        eng = self.engine

        def ff(*a, **ka):
            func_ptr = eng.get_function_address(entry_point)
            cfunc = cfunctype(func_ptr)
            try:
                return cfunc(*a, **ka)
            except ArgumentError:
                raise JitTypeError


        ff.restype = func.return_jtype.to_ctype()

        return ff


jitengine = JitEngine()
