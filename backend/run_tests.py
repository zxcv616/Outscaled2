#!/usr/bin/env python3
"""
Test runner for Outscaled.GG Backend
Run all unit tests and generate coverage report
"""

import unittest
import sys
import os
import subprocess

def run_tests():
    """Run all backend tests"""
    print("TEST Running Outscaled.GG Backend Tests")
    print("=" * 50)
    
    # Add the app directory to the path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
    
    # Discover and run all tests
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(__file__), 'tests')
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print("SUMMARY Test Summary")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    if result.wasSuccessful():
        print("\nSUCCESS All tests passed!")
        return 0
    else:
        print("\nFAILED Some tests failed!")
        return 1

def run_pytest():
    """Run tests using pytest for better output"""
    try:
        print("TEST Running tests with pytest...")
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            'tests/', 
            '-v', 
            '--tb=short'
        ], cwd=os.path.dirname(__file__))
        return result.returncode
    except FileNotFoundError:
        print("WARNING pytest not found, falling back to unittest")
        return run_tests()

if __name__ == '__main__':
    # Try pytest first, fall back to unittest
    exit_code = run_pytest()
    sys.exit(exit_code) 