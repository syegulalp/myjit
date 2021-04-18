import llvmlite.binding as llvm
from ctypes import CFUNCTYPE


class JitEngine:
    def __init__(self):
        llvm.initialize()
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()
        self.create_execution_engine()
        self.modules = {}
        self.mod = None

    def create_execution_engine(self):
        # Create a target machine representing the host
        target = llvm.Target.from_default_triple()
        target_machine = target.create_target_machine()
        # And an execution engine with an empty backing module
        backing_mod = llvm.parse_assembly("")
        self.engine = llvm.create_mcjit_compiler(backing_mod, target_machine)
        self.pm = llvm.ModulePassManager()
        llvm.PassManagerBuilder().populate(self.pm)

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

    # link in other, preserve=False
    # other module not usable fater call
    # so, use anonymous commands?
    # or llvmlite.binding.add_symbol?

    def compile(self, codegen, opt_level=None, entry_point="main"):

        mod = self.compile_ir(str(codegen.module), opt_level)
        self.modules[codegen.py_module_name] = mod
        func_ptr = self.engine.get_function_address(entry_point)

        arg_types = [_.to_ctype() for _ in codegen.argtypes]

        func = codegen.module.globals[entry_point]
        cfunc = CFUNCTYPE(func.return_jtype.to_ctype(), *arg_types)(func_ptr)
        return cfunc

    def clear(self):
        self.engine.remove_module(self.mod)
        self.mod = None

    def load_bc(self, external, module):
        """
        Placeholder for loading `external` bitcode into jit
        and optionally merging with `module` (e.g., stdlib loading)
        """

    def save_bc(self, module):
        """
        Placeholder to write bitcode out
        """

    def load_asm(self):
        pass


jitengine = JitEngine()
