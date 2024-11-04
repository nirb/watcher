import unittest
from test.helper import test_printer


def run_tests():
    # Create a test loader
    loader = unittest.TestLoader()

    # Discover all test cases from the 'tests' directory
    tests = loader.discover(start_dir='', pattern='test_*.py')

    # Create a test runner
    runner = unittest.TextTestRunner(verbosity=2, failfast=True)

    # Run the tests
    test_printer("starting tests", 20)
    for t in tests:
        result = runner.run(t)
        print(result)
    exit(0)
