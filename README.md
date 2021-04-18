This is a prototype for a JIT/AOT framework that takes in a decorated Python function, written in a subset of Python's syntax, and generates a native binary using LLVM (specifically, with the `llvmlite` library).

This is an *extremely* simple proof-of-concept. It doesn't do very much yet. It  might eventually turn into something larger, but right now it's just an exploratory playground.

If you're interested in making something of it, get in touch.

# Rationale

This project grew out of an earlier attempt to use Python to create a compiler for a toy language. I actually got fairly far along with that project, but left it behind for other things.

When I came back to it, I decided it might be more interesting to use a subset of Python as the base language, instead of one I'd wheel-reinvented. It made sense to leverage Python's own AST mechanisms, and Python's own syntax, since we already got all those for free with Python.

# Usage

When you decorate a function with the `@jit` decorator, it's transformed into machine-native assembly when the module is loaded. Execute the function, and the decorator will execute the assembly in lieu of the original code, and return a result.

In time this functionality could be expanded to AOT compilation as well. For instance, one could feed it a function and have a binary generated and deployed side-by-side with one's Python code, with some convenience functions provided by the compiler to wrap the binary and use it in your code. (It might also be possible to feed it an entire code tree and compile that, but that's a long way off.)

Right now very few operations are supported. The JIT can only perform basic arithmetic on bytes, store them in variables, and return the results. It does not yet reliably trap type errors or perform other checking (yet).

# Quickstart

Clone the repo and install requirements from `requirements.txt`.

The test suite (run `python .\tests\`) should run through the complete feature set.

# License

MIT