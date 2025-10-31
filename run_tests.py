#!/usr/bin/env python
"""
Simple test runner script that can be executed directly.
"""

import sys
import unittest

# Run the test suite
if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.discover('.', pattern='test_*.py')
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
