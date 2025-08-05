#!/usr/bin/env python3
"""
FEATURE VALIDATION TEST RUNNER

This script runs all feature validation tests and provides detailed reporting
of validation results after ML pipeline fixes are implemented.

USAGE:
======
python run_feature_validation_tests.py [--verbose] [--specific-test TEST_NAME]

FEATURES:
=========
- Runs all feature validation test suites
- Provides detailed pass/fail reporting
- Highlights critical failures that indicate incomplete fixes
- Generates summary report for validation status
- Can run specific test categories or individual tests

TEST CATEGORIES:
===============
1. Feature Extraction Validation (test_feature_validation.py)
2. Position Filtering Validation (test_position_filtering_validation.py)

EXPECTED RESULTS:
================
BEFORE FIXES: Many tests will fail due to inconsistent feature extraction
AFTER FIXES: All tests should pass, indicating consistent pipeline behavior
"""

import unittest
import sys
import os
import argparse
from io import StringIO
import traceback
from datetime import datetime

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def colored_output(text, color):
    """Add color to console output"""
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'end': '\033[0m'
    }
    return f"{colors.get(color, '')}{text}{colors['end']}"

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*80)
    print(colored_output(f" {title} ", 'cyan'))
    print("="*80)

def print_section(title):
    """Print a formatted section header"""
    print("\n" + colored_output(f"--- {title} ---", 'blue'))

def run_test_suite(test_module_name, verbose=False):
    """Run a specific test suite and return results"""
    print_section(f"Running {test_module_name}")
    
    try:
        # Import the test module
        test_module = __import__(f'tests.{test_module_name}', fromlist=[''])
        
        # Create test suite
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(test_module)
        
        # Run tests with custom result capturing
        stream = StringIO()
        runner = unittest.TextTestRunner(
            stream=stream,
            verbosity=2 if verbose else 1,
            failfast=False
        )
        
        result = runner.run(suite)
        
        # Get output
        output = stream.getvalue()
        
        # Print results
        if verbose:
            print(output)
        
        # Summary
        total_tests = result.testsRun
        failures = len(result.failures)
        errors = len(result.errors)
        passed = total_tests - failures - errors
        
        print(f"\nResults for {test_module_name}:")
        print(f"  {colored_output('✓ Passed:', 'green')} {passed}")
        if failures > 0:
            print(f"  {colored_output('✗ Failed:', 'red')} {failures}")
        if errors > 0:
            print(f"  {colored_output('⚠ Errors:', 'yellow')} {errors}")
        
        # Show failures and errors
        if failures > 0:
            print(f"\n{colored_output('FAILURES:', 'red')}")
            for test, traceback in result.failures:
                print(f"  - {test}")
                if verbose:
                    print(f"    {traceback.splitlines()[-1]}")
        
        if errors > 0:
            print(f"\n{colored_output('ERRORS:', 'yellow')}")
            for test, traceback in result.errors:
                print(f"  - {test}")
                if verbose:
                    print(f"    {traceback.splitlines()[-1]}")
        
        return {
            'module': test_module_name,
            'total': total_tests,
            'passed': passed,
            'failed': failures,
            'errors': errors,
            'success_rate': (passed / total_tests * 100) if total_tests > 0 else 0,
            'failures': result.failures,
            'errors': result.errors
        }
        
    except Exception as e:
        print(f"{colored_output('ERROR loading test module:', 'red')} {test_module_name}")
        print(f"  {str(e)}")
        traceback.print_exc()
        return {
            'module': test_module_name,
            'total': 0,
            'passed': 0,
            'failed': 0,
            'errors': 1,
            'success_rate': 0,
            'failures': [],
            'errors': [(test_module_name, str(e))]
        }

def run_specific_test(test_path, verbose=False):
    """Run a specific test method"""
    print_section(f"Running specific test: {test_path}")
    
    try:
        # Parse test path (module.class.method)
        parts = test_path.split('.')
        if len(parts) < 2:
            print(f"{colored_output('ERROR:', 'red')} Invalid test path format. Use module.class.method")
            return None
        
        module_name = parts[0]
        test_name = '.'.join(parts[1:])
        
        # Load and run specific test
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName(test_name, __import__(f'tests.{module_name}', fromlist=['']))
        
        stream = StringIO()
        runner = unittest.TextTestRunner(
            stream=stream,
            verbosity=2 if verbose else 1
        )
        
        result = runner.run(suite)
        
        if verbose:
            print(stream.getvalue())
        
        success = result.wasSuccessful()
        print(f"Test result: {colored_output('PASSED' if success else 'FAILED', 'green' if success else 'red')}")
        
        return success
        
    except Exception as e:
        print(f"{colored_output('ERROR running specific test:', 'red')} {e}")
        traceback.print_exc()
        return False

def generate_summary_report(results):
    """Generate a comprehensive summary report"""
    print_header("FEATURE VALIDATION TEST SUMMARY REPORT")
    
    total_tests = sum(r['total'] for r in results)
    total_passed = sum(r['passed'] for r in results)
    total_failed = sum(r['failed'] for r in results)
    total_errors = sum(r['errors'] for r in results)
    
    overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Test Suites: {len(results)}")
    print(f"Total Tests: {total_tests}")
    print(f"Overall Success Rate: {overall_success_rate:.1f}%")
    
    print(f"\n{colored_output('OVERALL RESULTS:', 'white')}")
    print(f"  {colored_output('✓ Passed:', 'green')} {total_passed}")
    print(f"  {colored_output('✗ Failed:', 'red')} {total_failed}")
    print(f"  {colored_output('⚠ Errors:', 'yellow')} {total_errors}")
    
    # Per-suite breakdown
    print(f"\n{colored_output('PER-SUITE BREAKDOWN:', 'white')}")
    for result in results:
        status_color = 'green' if result['success_rate'] == 100 else ('yellow' if result['success_rate'] > 50 else 'red')
        print(f"  {result['module']}: {colored_output(f'{result[\"success_rate\"]:.1f}%', status_color)} "
              f"({result['passed']}/{result['total']})")
    
    # Critical analysis
    print(f"\n{colored_output('CRITICAL ANALYSIS:', 'white')}")
    
    if overall_success_rate == 100:
        print(colored_output("🎉 ALL TESTS PASSING - ML Pipeline fixes appear to be complete!", 'green'))
    elif overall_success_rate >= 90:
        print(colored_output("✅ Most tests passing - Minor issues remain", 'yellow'))
    elif overall_success_rate >= 70:
        print(colored_output("⚠️  Significant issues detected - More fixes needed", 'yellow'))
    else:
        print(colored_output("🚨 MAJOR ISSUES - ML Pipeline fixes incomplete", 'red'))
    
    # Specific recommendations
    print(f"\n{colored_output('RECOMMENDATIONS:', 'white')}")
    
    if total_failed > 0:
        print("❌ Failed Tests Indicate:")
        print("   - Feature extraction inconsistency between training/prediction")
        print("   - Position filtering not working correctly")
        print("   - Edge case handling issues")
        print("   - Combined vs average statistics logic problems")
    
    if total_errors > 0:
        print("⚠️  Errors Indicate:")
        print("   - Missing or broken imports")
        print("   - Code structure issues")
        print("   - Runtime exceptions in feature extraction")
    
    # Next steps
    print(f"\n{colored_output('NEXT STEPS:', 'white')}")
    if overall_success_rate < 100:
        print("1. Review failed test details for specific issues")
        print("2. Fix identified problems in feature extraction pipeline")
        print("3. Re-run tests to validate fixes")
        print("4. Focus on consistency between training and prediction paths")
    else:
        print("1. All validation tests passing - pipeline is consistent")
        print("2. Ready for production deployment")
        print("3. Monitor for any regression in feature extraction")
    
    return overall_success_rate >= 90  # Return True if mostly successful

def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description='Run feature validation tests')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Verbose output with detailed test results')
    parser.add_argument('--specific-test', '-t', type=str,
                       help='Run specific test (format: module.class.method)')
    parser.add_argument('--suite', '-s', type=str,
                       help='Run specific test suite only')
    
    args = parser.parse_args()
    
    print_header("FEATURE VALIDATION TEST RUNNER")
    print("This runner validates ML pipeline consistency after fixes")
    print(f"Verbose mode: {args.verbose}")
    
    if args.specific_test:
        # Run specific test
        success = run_specific_test(args.specific_test, args.verbose)
        sys.exit(0 if success else 1)
    
    # Define test suites to run
    test_suites = [
        'test_feature_validation',
        'test_position_filtering_validation'
    ]
    
    if args.suite:
        if args.suite in test_suites:
            test_suites = [args.suite]
        else:
            print(f"{colored_output('ERROR:', 'red')} Unknown test suite: {args.suite}")
            print(f"Available suites: {', '.join(test_suites)}")
            sys.exit(1)
    
    # Run all test suites
    results = []
    for suite in test_suites:
        result = run_test_suite(suite, args.verbose)
        results.append(result)
    
    # Generate summary report
    overall_success = generate_summary_report(results)
    
    # Exit with appropriate code
    sys.exit(0 if overall_success else 1)

if __name__ == '__main__':
    main()