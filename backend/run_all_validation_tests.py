#!/usr/bin/env python3
"""
COMPREHENSIVE VALIDATION TEST RUNNER
====================================

This script runs all validation test suites and provides a comprehensive
report on the prediction system's reliability and consistency.

Test Suites:
1. Core prediction validation
2. Edge cases and boundary conditions  
3. Performance and consistency validation
"""

import sys
import os
import subprocess
import time
from typing import Dict, List, Tuple

def run_test_suite(test_file: str, suite_name: str) -> Dict[str, any]:
    """Run a test suite and capture results"""
    print(f"\n{'='*80}")
    print(f"RUNNING: {suite_name}")
    print(f"{'='*80}")
    
    start_time = time.time()
    
    try:
        # Run the test file
        result = subprocess.run(
            [sys.executable, test_file],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Parse output for test results
        output_lines = result.stdout.split('\n')
        error_lines = result.stderr.split('\n')
        
        # Look for test results in output
        tests_run = 0
        failures = 0
        errors = 0
        
        for line in output_lines:
            if 'Ran ' in line and ' test' in line:
                # Extract test count from "Ran X tests in Y.Zs"
                parts = line.split()
                if len(parts) > 1:
                    try:
                        tests_run = int(parts[1])
                    except ValueError:
                        pass
            elif 'FAILED (' in line:
                # Extract failure/error counts
                if 'failures=' in line:
                    failures_str = line.split('failures=')[1].split(',')[0].split(')')[0]
                    try:
                        failures = int(failures_str)
                    except ValueError:
                        pass
                if 'errors=' in line:
                    errors_str = line.split('errors=')[1].split(',')[0].split(')')[0]
                    try:
                        errors = int(errors_str)
                    except ValueError:
                        pass
        
        success = result.returncode == 0 and failures == 0 and errors == 0
        
        return {
            'suite_name': suite_name,
            'success': success,
            'duration': duration,
            'tests_run': tests_run,
            'failures': failures,
            'errors': errors,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'return_code': result.returncode
        }
        
    except subprocess.TimeoutExpired:
        return {
            'suite_name': suite_name,
            'success': False,
            'duration': 300,
            'tests_run': 0,
            'failures': 0,
            'errors': 1,
            'stdout': '',
            'stderr': 'Test suite timed out after 5 minutes',
            'return_code': -1
        }
    except Exception as e:
        return {
            'suite_name': suite_name,
            'success': False,
            'duration': 0,
            'tests_run': 0,
            'failures': 0,
            'errors': 1,
            'stdout': '',
            'stderr': f'Failed to run test suite: {str(e)}',
            'return_code': -1
        }

def print_summary(results: List[Dict]) -> bool:
    """Print comprehensive summary of all test results"""
    print(f"\n{'='*80}")
    print("COMPREHENSIVE VALIDATION SUMMARY")
    print(f"{'='*80}")
    
    total_tests = sum(r['tests_run'] for r in results)
    total_failures = sum(r['failures'] for r in results)
    total_errors = sum(r['errors'] for r in results)
    total_duration = sum(r['duration'] for r in results)
    
    successful_suites = sum(1 for r in results if r['success'])
    total_suites = len(results)
    
    print(f"Overall Results:")
    print(f"  Test Suites: {successful_suites}/{total_suites} passed")
    print(f"  Total Tests: {total_tests}")
    print(f"  Failures: {total_failures}")
    print(f"  Errors: {total_errors}")
    print(f"  Total Duration: {total_duration:.2f}s")
    print()
    
    # Suite-by-suite breakdown
    print("Suite Breakdown:")
    print("-" * 80)
    
    for result in results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"  {result['suite_name']:<40} {status}")
        print(f"    Tests: {result['tests_run']:<3} | Failures: {result['failures']:<3} | Errors: {result['errors']:<3} | Time: {result['duration']:.2f}s")
        
        if not result['success']:
            print(f"    Issues:")
            if result['failures'] > 0:
                print(f"      - {result['failures']} test failures")
            if result['errors'] > 0:
                print(f"      - {result['errors']} test errors")
            if result['return_code'] != 0:
                print(f"      - Non-zero exit code: {result['return_code']}")
        print()
    
    # Detailed failure information
    failed_suites = [r for r in results if not r['success']]
    if failed_suites:
        print("FAILURE DETAILS:")
        print("-" * 80)
        
        for result in failed_suites:
            print(f"\n{result['suite_name']} FAILURES:")
            if result['stderr'].strip():
                print("STDERR:")
                print(result['stderr'][:1000])  # Limit output
            if result['stdout'].strip():
                print("STDOUT (last 1000 chars):")
                print(result['stdout'][-1000:])
    
    # Overall assessment
    print(f"\n{'='*80}")
    overall_success = all(r['success'] for r in results)
    if overall_success:
        print("🎉 ALL VALIDATION TESTS PASSED!")
        print("The prediction system meets all reliability and consistency requirements.")
    else:
        print("⚠️  SOME VALIDATION TESTS FAILED")
        print("The prediction system has issues that need to be addressed.")
        print(f"Failed suites: {', '.join([r['suite_name'] for r in failed_suites])}")
    
    print(f"{'='*80}")
    
    return overall_success

def main():
    """Run all validation test suites"""
    print("STARTING COMPREHENSIVE VALIDATION")
    print(f"{'='*80}")
    print("This will run all validation test suites to ensure prediction system reliability.")
    print("Estimated time: 2-5 minutes depending on system performance.")
    print()
    
    # Define test suites
    test_suites = [
        ("test_prediction_validation.py", "Core Prediction Validation"),
        ("test_edge_cases_validation.py", "Edge Cases & Boundary Conditions"),
        ("test_performance_validation.py", "Performance & Consistency")
    ]
    
    results = []
    start_time = time.time()
    
    # Run each test suite
    for test_file, suite_name in test_suites:
        if os.path.exists(test_file):
            result = run_test_suite(test_file, suite_name)
            results.append(result)
        else:
            print(f"❌ Test file not found: {test_file}")
            results.append({
                'suite_name': suite_name,
                'success': False,
                'duration': 0,
                'tests_run': 0,
                'failures': 0,
                'errors': 1,
                'stdout': '',
                'stderr': f'Test file not found: {test_file}',
                'return_code': -1
            })
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Print comprehensive summary
    overall_success = print_summary(results)
    
    print(f"\nValidation completed in {total_time:.2f}s")
    
    # Exit with appropriate code
    sys.exit(0 if overall_success else 1)

if __name__ == '__main__':
    main()