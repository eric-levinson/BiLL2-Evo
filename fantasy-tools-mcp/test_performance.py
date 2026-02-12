"""
Performance test for get_metrics_metadata() function.
Tests execution time to verify <1ms per call (down from 5-10ms with dynamic import).
"""

import timeit
import statistics

def run_performance_test():
    """
    Measures execution time of get_metrics_metadata() over multiple calls.
    Compares against expected <1ms performance target.
    """

    # Test setup
    setup_code = "from tools.metrics.info import get_metrics_metadata"

    # Test cases covering different categories and subcategories
    test_cases = [
        ("get_metrics_metadata('receiving', 'volume_metrics')", "Receiving - Volume Metrics"),
        ("get_metrics_metadata('passing', 'efficiency_metrics')", "Passing - Efficiency Metrics"),
        ("get_metrics_metadata('rushing', 'situational_metrics')", "Rushing - Situational Metrics"),
        ("get_metrics_metadata('defense', 'basic_info')", "Defense - Basic Info"),
        ("get_metrics_metadata('receiving', None)", "Receiving - Full Category"),
    ]

    print("=" * 70)
    print("Performance Test: get_metrics_metadata()")
    print("=" * 70)
    print(f"\nTarget: <1ms per call (down from 5-10ms with dynamic import)\n")

    results = []

    for test_code, description in test_cases:
        # Run 1000 iterations to get accurate timing
        iterations = 1000
        total_time = timeit.timeit(test_code, setup=setup_code, number=iterations)
        avg_time_ms = (total_time / iterations) * 1000  # Convert to milliseconds

        results.append(avg_time_ms)

        status = "✓ PASS" if avg_time_ms < 1.0 else "✗ FAIL"
        print(f"{status} | {description:40s} | {avg_time_ms:.4f} ms/call")

    print("\n" + "=" * 70)
    print("Summary Statistics")
    print("=" * 70)

    avg_ms = statistics.mean(results)
    min_ms = min(results)
    max_ms = max(results)
    median_ms = statistics.median(results)
    stdev_ms = statistics.stdev(results) if len(results) > 1 else 0

    print(f"Average:        {avg_ms:.4f} ms")
    print(f"Median:         {median_ms:.4f} ms")
    print(f"Min:            {min_ms:.4f} ms")
    print(f"Max:            {max_ms:.4f} ms")
    print(f"Std Dev:        {stdev_ms:.4f} ms")

    print("\n" + "=" * 70)

    # Overall pass/fail
    if avg_ms < 1.0:
        print(f"✓ PERFORMANCE TEST PASSED")
        print(f"  Average execution time ({avg_ms:.4f} ms) is well below 1ms target")
        print(f"  Estimated improvement: ~{5/avg_ms:.1f}x-{10/avg_ms:.1f}x faster than dynamic import (5-10ms)")
        return True
    else:
        print(f"✗ PERFORMANCE TEST FAILED")
        print(f"  Average execution time ({avg_ms:.4f} ms) exceeds 1ms target")
        return False

if __name__ == "__main__":
    success = run_performance_test()
    exit(0 if success else 1)
