#!/usr/bin/env python3
"""
Comprehensive Memory System Test Runner

This script runs all memory system tests and generates a complete report
with pass/fail statistics and detailed results.
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from test_result_logger import get_test_results, generate_html_report

def run_pytest_file(test_file):
    """Run a single pytest file and return the results."""
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            str(test_file), 
            "-v", 
            "--tb=short"
        ], capture_output=True, text=True, cwd=project_root)
        
        return {
            "file": test_file.name,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
    except Exception as e:
        return {
            "file": test_file.name,
            "return_code": -1,
            "stdout": "",
            "stderr": str(e),
            "success": False
        }

def get_all_test_files():
    """Get all test files in the tests directory."""
    tests_dir = project_root / "tests"
    test_files = []
    
    for test_file in tests_dir.glob("test_*.py"):
        if test_file.name != "run_all_tests.py":
            test_files.append(test_file)
    
    return sorted(test_files)

def run_all_tests():
    """Run all memory system tests and generate comprehensive report."""
    print("🚀 Starting Comprehensive Memory System Test Suite")
    print("=" * 60)
    
    # Get all test files
    test_files = get_all_test_files()
    print(f"📁 Found {len(test_files)} test files:")
    for test_file in test_files:
        print(f"   • {test_file.name}")
    
    print("\n" + "=" * 60)
    print("🧪 Running Tests...")
    print("=" * 60)
    
    # Run each test file
    test_results = []
    start_time = time.time()
    
    for i, test_file in enumerate(test_files, 1):
        print(f"\n[{i}/{len(test_files)}] Running {test_file.name}...")
        
        result = run_pytest_file(test_file)
        test_results.append(result)
        
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"   {status} - {test_file.name}")
        
        if not result["success"] and result["stderr"]:
            print(f"   Error: {result['stderr'][:200]}...")
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Generate summary statistics
    total_tests = len(test_results)
    passed_tests = sum(1 for r in test_results if r["success"])
    failed_tests = total_tests - passed_tests
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Total Test Files: {total_tests}")
    print(f"Passed: {passed_tests} ✅")
    print(f"Failed: {failed_tests} ❌")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    print(f"Total Time: {total_time:.2f} seconds")
    
    # Get detailed test results from logger
    detailed_results = get_test_results()
    
    # Generate comprehensive report
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_test_files": total_tests,
            "passed_test_files": passed_tests,
            "failed_test_files": failed_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "total_time_seconds": total_time
        },
        "test_file_results": test_results,
        "detailed_test_results": detailed_results,
        "failed_tests": [
            r for r in test_results if not r["success"]
        ]
    }
    
    # Save JSON report
    report_file = project_root / "test_results" / "comprehensive_test_report.json"
    report_file.parent.mkdir(exist_ok=True)
    
    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\n📄 Detailed JSON report saved to: {report_file}")
    
    # Generate HTML report
    html_report_file = project_root / "test_results" / "comprehensive_test_report.html"
    generate_html_report(report_data, html_report_file)
    print(f"📄 HTML report saved to: {html_report_file}")
    
    # Show failed tests details
    if failed_tests > 0:
        print("\n" + "=" * 60)
        print("❌ FAILED TESTS DETAILS")
        print("=" * 60)
        
        for result in test_results:
            if not result["success"]:
                print(f"\n🔴 {result['file']}:")
                if result["stderr"]:
                    print(f"   Error: {result['stderr'][:500]}...")
                if result["stdout"]:
                    print(f"   Output: {result['stdout'][:200]}...")
    
    # Show detailed test results
    if detailed_results:
        print("\n" + "=" * 60)
        print("📋 DETAILED TEST RESULTS")
        print("=" * 60)
        
        for test_name, result in detailed_results.items():
            status = "✅" if result["status"] == "pass" else "❌"
            print(f"{status} {test_name}")
    
    print("\n" + "=" * 60)
    print("🎉 Test Suite Complete!")
    print("=" * 60)
    
    if failed_tests == 0:
        print("🎊 All tests passed! Memory system is working correctly.")
        return 0
    else:
        print(f"⚠️  {failed_tests} test files failed. Please review the detailed reports.")
        return 1

def main():
    """Main entry point."""
    try:
        exit_code = run_all_tests()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⏹️  Test execution interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 