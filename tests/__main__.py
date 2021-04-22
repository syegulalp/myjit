import unittest

import sys

sys.path.insert(0, ".\\")


def main():
    print("Discovering tests.")
    tests = unittest.TestLoader().discover(".\\tests", pattern="test_*.py")
    print("Starting.")
    unittest.TextTestRunner(failfast=True).run(tests)


if __name__ == "__main__":
    main()


# TODO (For implemented features)
# arrays
# signed/unsigned behaviors
# eventually:
# programmatic generation of tests
