#!/usr/bin/env python3
"""
Stack 2.9 - Test Runner
All-in-one test runner: Unit → Integration → Benchmarks
with JUnit XML output and coverage reporting.
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path
from typing import List, Optional


# Ensure stack_cli is in path
stack_cli_dir = Path(__file__).parent.parent / "stack_cli"
if str(stack_cli_dir) not in sys.path:
    sys.path.insert(0, str(stack_cli_dir))


def run_pytest(
    args: List[str],
    capture_output: bool = True,
    env: Optional[dict] = None
) -> subprocess.CompletedProcess:
    """Run pytest with given arguments."""
    cmd = [sys.executable, "-m", "pytest"] + args
    
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    
    return subprocess.run(
        cmd,
        capture_output=capture_output,
        text=True,
        env=run_env,
        cwd=Path(__file__).parent
    )


def run_unit_tests(verbose: bool = True, markers: Optional[str] = None) -> int:
    """Run unit tests."""
    print("\n" + "="*60)
    print("Running Unit Tests")
    print("="*60)
    
    args = ["tests/unit/"]
    
    if verbose:
        args.append("-v")
    
    if markers:
        args.extend(["-m", markers])
    
    result = run_pytest(args)
    
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    return result.returncode


def run_integration_tests(verbose: bool = True, markers: Optional[str] = None) -> int:
    """Run integration tests."""
    print("\n" + "="*60)
    print("Running Integration Tests")
    print("="*60)
    
    args = ["tests/integration/"]
    
    if verbose:
        args.append("-v")
    
    if markers:
        args.extend(["-m", markers])
    
    result = run_pytest(args)
    
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    return result.returncode


def run_benchmark_tests(verbose: bool = True) -> int:
    """Run benchmark tests."""
    print("\n" + "="*60)
    print("Running Benchmark Tests")
    print("="*60)
    
    args = ["tests/benchmarks/", "-v"]
    
    result = run_pytest(args)
    
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    return result.returncode


def run_all_tests(
    verbose: bool = True,
    junit_xml: Optional[str] = None,
    coverage: bool = False,
    markers: Optional[str] = None
) -> int:
    """Run all tests."""
    print("\n" + "#"*60)
    print("# Stack 2.9 - Test Suite")
    print("#"*60)
    
    results = []
    
    # Unit tests
    print("\n[1/3] Unit Tests...")
    unit_result = run_unit_tests(verbose=verbose, markers=markers)
    results.append(("Unit Tests", unit_result))
    
    # Integration tests
    print("\n[2/3] Integration Tests...")
    int_result = run_integration_tests(verbose=verbose, markers=markers)
    results.append(("Integration Tests", int_result))
    
    # Benchmark tests
    print("\n[3/3] Benchmark Tests...")
    bench_result = run_benchmark_tests(verbose=verbose)
    results.append(("Benchmark Tests", bench_result))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    all_passed = True
    for name, code in results:
        status = "✓ PASSED" if code == 0 else "✗ FAILED"
        print(f"  {name}: {status}")
        if code != 0:
            all_passed = False
    
    print("="*60)
    
    if all_passed:
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed!")
        return 1


def run_with_coverage() -> int:
    """Run tests with coverage reporting."""
    print("\n" + "="*60)
    print("Running Tests with Coverage")
    print("="*60)
    
    args = [
        "tests/",
        "--cov=stack_cli",
        "--cov-report=term-missing",
        "--cov-report=html",
        "-v"
    ]
    
    result = run_pytest(args)
    
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    return result.returncode


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Stack 2.9 Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Run all tests
  %(prog)s --unit             # Run only unit tests
  %(prog)s --integration      # Run only integration tests
  %(prog)s --benchmark        # Run only benchmark tests
  %(prog)s --coverage         # Run with coverage
  %(prog)s --junit results.xml  # Generate JUnit XML
  %(prog)s --fast             # Skip slow tests
        """
    )
    
    parser.add_argument(
        '--unit',
        action='store_true',
        help='Run only unit tests'
    )
    
    parser.add_argument(
        '--integration',
        action='store_true',
        help='Run only integration tests'
    )
    
    parser.add_argument(
        '--benchmark',
        action='store_true',
        help='Run only benchmark tests'
    )
    
    parser.add_argument(
        '--coverage',
        action='store_true',
        help='Run with coverage reporting'
    )
    
    parser.add_argument(
        '--junit',
        metavar='FILE',
        help='Generate JUnit XML output'
    )
    
    parser.add_argument(
        '--fast',
        action='store_true',
        help='Skip slow tests'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        default=True,
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    # Build pytest args
    pytest_args = []
    
    if args.junit:
        pytest_args.extend(['--junit-xml', args.junit])
    
    if args.fast:
        pytest_args.extend(['-m', 'not slow'])
    
    # Run tests based on options
    if args.unit:
        return run_unit_tests(verbose=args.verbose, markers=args.fast and 'not slow' or None)
    
    elif args.integration:
        return run_integration_tests(verbose=args.verbose, markers=args.fast and 'not slow' or None)
    
    elif args.benchmark:
        return run_benchmark_tests(verbose=args.verbose)
    
    elif args.coverage:
        return run_with_coverage()
    
    else:
        # Run all tests
        return run_all_tests(
            verbose=args.verbose,
            junit_xml=args.junit,
            markers=args.fast and 'not slow' or None
        )


if __name__ == "__main__":
    sys.exit(main())
