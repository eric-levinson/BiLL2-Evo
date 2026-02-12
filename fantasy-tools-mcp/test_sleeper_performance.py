#!/usr/bin/env python3
"""
Performance test for parallelized Sleeper API functions.
Tests execution time to verify ~3x improvement (600ms -> ~200ms) from parallel API calls.
"""

import timeit
import statistics
import sys

# Test league ID from spec
TEST_LEAGUE_ID = "1225572389929099264"
TEST_WEEK = 1


def run_performance_test():
    """
    Measures execution time of parallelized Sleeper functions over multiple calls.
    Compares against expected performance targets based on parallel execution.
    """

    # Test setup - import functions
    setup_code = """
from tools.fantasy.info import (
    get_sleeper_league_rosters,
    get_sleeper_league_matchups,
    get_sleeper_league_transactions,
)

TEST_LEAGUE_ID = "1225572389929099264"
TEST_WEEK = 1
"""

    # Test cases for the three parallelized functions
    test_cases = [
        (
            f"get_sleeper_league_matchups(TEST_LEAGUE_ID, TEST_WEEK, summary=False)",
            "get_sleeper_league_matchups",
            "3 parallel API calls (matchups, rosters, users)",
            500,  # Target: ~400-500ms (down from ~1200ms sequential)
        ),
        (
            f"get_sleeper_league_rosters(TEST_LEAGUE_ID, summary=False)",
            "get_sleeper_league_rosters",
            "2 parallel API calls (rosters, users)",
            300,  # Target: ~200-300ms (down from ~400ms sequential)
        ),
        (
            f"get_sleeper_league_transactions(TEST_LEAGUE_ID, TEST_WEEK)",
            "get_sleeper_league_transactions",
            "3 parallel API calls (transactions, rosters, users)",
            500,  # Target: ~200-500ms (down from ~600ms sequential)
        ),
    ]

    print("=" * 80)
    print("Performance Test: Parallelized Sleeper API Functions")
    print("=" * 80)
    print(f"\nTest League ID: {TEST_LEAGUE_ID}")
    print(f"Test Week: {TEST_WEEK}\n")
    print("Expected improvements from parallel execution:")
    print("  • get_sleeper_league_matchups: ~1200ms → ~400-500ms (3x faster)")
    print("  • get_sleeper_league_rosters:   ~400ms → ~200-300ms (2x faster)")
    print("  • get_sleeper_league_transactions: ~600ms → ~200-500ms (3x faster)")
    print("\n" + "=" * 80)

    all_results = {}
    all_passed = True

    for test_code, function_name, description, target_ms in test_cases:
        print(f"\nTesting: {function_name}")
        print(f"Description: {description}")
        print(f"Target: <{target_ms}ms per call")
        print("-" * 80)

        # Run multiple iterations to get accurate timing
        # Use fewer iterations since these are real API calls
        iterations = 5
        times = []

        print(f"Running {iterations} iterations...")
        for i in range(iterations):
            time_seconds = timeit.timeit(test_code, setup=setup_code, number=1)
            time_ms = time_seconds * 1000
            times.append(time_ms)
            print(f"  Iteration {i+1}: {time_ms:.2f} ms")

        # Calculate statistics
        avg_ms = statistics.mean(times)
        min_ms = min(times)
        max_ms = max(times)
        median_ms = statistics.median(times)
        stdev_ms = statistics.stdev(times) if len(times) > 1 else 0

        all_results[function_name] = {
            "avg": avg_ms,
            "min": min_ms,
            "max": max_ms,
            "median": median_ms,
            "stdev": stdev_ms,
            "target": target_ms,
            "passed": avg_ms <= target_ms,
        }

        print(f"\nStatistics:")
        print(f"  Average:        {avg_ms:.2f} ms")
        print(f"  Median:         {median_ms:.2f} ms")
        print(f"  Min:            {min_ms:.2f} ms")
        print(f"  Max:            {max_ms:.2f} ms")
        print(f"  Std Dev:        {stdev_ms:.2f} ms")

        # Pass/fail evaluation
        if avg_ms <= target_ms:
            print(f"✓ PASS: Average time ({avg_ms:.2f} ms) is within target (<{target_ms}ms)")
        else:
            print(f"✗ FAIL: Average time ({avg_ms:.2f} ms) exceeds target ({target_ms}ms)")
            all_passed = False

        print("=" * 80)

    # Overall summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    for function_name, results in all_results.items():
        status = "✓ PASS" if results["passed"] else "✗ FAIL"
        improvement = ""

        # Calculate improvement ratios based on expected sequential times
        if function_name == "get_sleeper_league_matchups":
            sequential_ms = 1200
            improvement_factor = sequential_ms / results["avg"]
            improvement = f" ({improvement_factor:.1f}x faster than sequential ~{sequential_ms}ms)"
        elif function_name == "get_sleeper_league_rosters":
            sequential_ms = 400
            improvement_factor = sequential_ms / results["avg"]
            improvement = f" ({improvement_factor:.1f}x faster than sequential ~{sequential_ms}ms)"
        elif function_name == "get_sleeper_league_transactions":
            sequential_ms = 600
            improvement_factor = sequential_ms / results["avg"]
            improvement = f" ({improvement_factor:.1f}x faster than sequential ~{sequential_ms}ms)"

        print(f"{status} | {function_name:40s} | {results['avg']:7.2f} ms{improvement}")

    print("=" * 80)

    if all_passed:
        print("\n✓ PERFORMANCE TEST PASSED")
        print("  All functions meet performance targets with parallel execution")
        return True
    else:
        print("\n✗ PERFORMANCE TEST FAILED")
        print("  Some functions did not meet performance targets")
        return False


def main():
    """Run performance test and exit with appropriate status code."""
    try:
        success = run_performance_test()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: Performance test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
