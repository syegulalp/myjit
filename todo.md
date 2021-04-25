* `range` function
  * iterator object
    * objects and bound methods
      * ability to mangle names for things
        * special name mangling decorator
          * store items to mangle in dict, reference by object
          * implement name mangling
        * `exec()` function calls a mangled function with arguments passed
* `gep()`
* `ref()`, `deref()`
  * the Python versions of these operate on their Py object counterparts if possible
* 

* convert to loadable C modules, obviate need for interface?

# TODO (For implemented features)
# arrays
# signed/unsigned behaviors
# eventually:
# programmatic generation of tests

# TODO:
# range() - implement as our first example of an iterator
# range.__iter__
# returns object with start, stop, step
# range.__next__
# objects
# functions that can be used as stdlib, like range - decorate with @rename("range.__next__")
