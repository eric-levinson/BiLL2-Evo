"""
Configuration Verification Test for Sleeper API Retry Logic

Tests that all environment variables properly override default configuration:
- RETRY_MAX_ATTEMPTS
- RETRY_INITIAL_DELAY_MS
- RETRY_MAX_DELAY_MS
- RETRY_BACKOFF_MULTIPLIER
"""

import os
import sys
import time
import unittest
from unittest.mock import Mock, patch
import requests

# Add parent directory to path so we can import from fantasy-tools-mcp root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from helpers.retry_utils import retry_with_backoff, is_retryable_http_error


class ConfigVerificationTest(unittest.TestCase):
    """Test suite for verifying environment variable configuration."""

    def setUp(self):
        """Clear environment variables before each test."""
        # Clear all retry-related env vars
        for var in ['RETRY_MAX_ATTEMPTS', 'RETRY_INITIAL_DELAY_MS',
                    'RETRY_MAX_DELAY_MS', 'RETRY_BACKOFF_MULTIPLIER']:
            if var in os.environ:
                del os.environ[var]

    def tearDown(self):
        """Clean up environment variables after each test."""
        self.setUp()  # Reuse setUp cleanup logic

    def test_retry_max_attempts(self):
        """Test RETRY_MAX_ATTEMPTS environment variable."""
        print("\n=== Test 1: RETRY_MAX_ATTEMPTS ===")

        # Set env var to 2 instead of default 3
        os.environ['RETRY_MAX_ATTEMPTS'] = '2'

        # Create a function that always fails and counts attempts
        attempt_count = {'value': 0}

        @retry_with_backoff()
        def always_fail():
            attempt_count['value'] += 1
            print(f"  Attempt {attempt_count['value']}")
            raise requests.exceptions.ConnectionError("Simulated connection error")

        # Should fail after 2 attempts
        try:
            always_fail()
            self.fail("Expected ConnectionError to be raised")
        except requests.exceptions.ConnectionError:
            print(f"  ConnectionError raised after {attempt_count['value']} attempts")
            self.assertEqual(attempt_count['value'], 2,
                           f"Expected 2 attempts, got {attempt_count['value']}")
            print("  ✓ PASS: RETRY_MAX_ATTEMPTS=2 correctly limited retries to 2 attempts")

    def test_retry_initial_delay_ms(self):
        """Test RETRY_INITIAL_DELAY_MS environment variable."""
        print("\n=== Test 2: RETRY_INITIAL_DELAY_MS ===")

        # Set initial delay to 200ms instead of default 1000ms
        os.environ['RETRY_INITIAL_DELAY_MS'] = '200'
        os.environ['RETRY_MAX_ATTEMPTS'] = '2'
        os.environ['RETRY_BACKOFF_MULTIPLIER'] = '1'  # No exponential growth

        attempt_count = {'value': 0}
        start_time = time.time()
        retry_times = []

        @retry_with_backoff()
        def always_fail():
            attempt_count['value'] += 1
            retry_times.append(time.time())
            print(f"  Attempt {attempt_count['value']}")
            raise requests.exceptions.ConnectionError("Simulated connection error")

        try:
            always_fail()
        except requests.exceptions.ConnectionError:
            # Calculate delay between first and second attempt
            if len(retry_times) >= 2:
                actual_delay_ms = (retry_times[1] - retry_times[0]) * 1000
                expected_delay_ms = 200
                tolerance_ms = 50

                print(f"  First retry delay: {actual_delay_ms:.0f}ms (expected: {expected_delay_ms}ms)")

                diff = abs(actual_delay_ms - expected_delay_ms)
                accuracy = ((expected_delay_ms - diff) / expected_delay_ms) * 100

                print(f"  Timing accuracy: {accuracy:.1f}% (diff: {diff:.0f}ms)")

                self.assertLess(diff, tolerance_ms,
                              f"Delay off by {diff:.0f}ms (tolerance: {tolerance_ms}ms)")
                print("  ✓ PASS: RETRY_INITIAL_DELAY_MS=200 correctly set initial delay to 200ms")

    def test_retry_backoff_multiplier(self):
        """Test RETRY_BACKOFF_MULTIPLIER environment variable."""
        print("\n=== Test 3: RETRY_BACKOFF_MULTIPLIER ===")

        # Set multiplier to 3 instead of default 2
        os.environ['RETRY_INITIAL_DELAY_MS'] = '100'
        os.environ['RETRY_BACKOFF_MULTIPLIER'] = '3'
        os.environ['RETRY_MAX_ATTEMPTS'] = '3'
        os.environ['RETRY_MAX_DELAY_MS'] = '10000'  # High max to not interfere

        attempt_count = {'value': 0}
        retry_times = []

        @retry_with_backoff()
        def always_fail():
            attempt_count['value'] += 1
            retry_times.append(time.time())
            print(f"  Attempt {attempt_count['value']}")
            raise requests.exceptions.ConnectionError("Simulated connection error")

        try:
            always_fail()
        except requests.exceptions.ConnectionError:
            # Verify delays follow 3x exponential backoff
            # Expected: 100ms, 300ms (100 * 3^1), 900ms (100 * 3^2)
            if len(retry_times) >= 3:
                delay1_ms = (retry_times[1] - retry_times[0]) * 1000
                delay2_ms = (retry_times[2] - retry_times[1]) * 1000

                expected_delay1 = 100
                expected_delay2 = 300
                tolerance = 50

                print(f"  Delay 1: {delay1_ms:.0f}ms (expected: {expected_delay1}ms)")
                print(f"  Delay 2: {delay2_ms:.0f}ms (expected: {expected_delay2}ms)")

                diff1 = abs(delay1_ms - expected_delay1)
                diff2 = abs(delay2_ms - expected_delay2)

                accuracy1 = ((expected_delay1 - diff1) / expected_delay1) * 100
                accuracy2 = ((expected_delay2 - diff2) / expected_delay2) * 100

                print(f"  Delay 1 accuracy: {accuracy1:.1f}% (diff: {diff1:.0f}ms)")
                print(f"  Delay 2 accuracy: {accuracy2:.1f}% (diff: {diff2:.0f}ms)")

                self.assertLess(diff1, tolerance, f"Delay 1 off by {diff1:.0f}ms")
                self.assertLess(diff2, tolerance, f"Delay 2 off by {diff2:.0f}ms")

                print("  ✓ PASS: RETRY_BACKOFF_MULTIPLIER=3 correctly applied 3x exponential backoff")

    def test_retry_max_delay_ms(self):
        """Test RETRY_MAX_DELAY_MS environment variable."""
        print("\n=== Test 4: RETRY_MAX_DELAY_MS ===")

        # Set max delay to 500ms to cap exponential growth
        os.environ['RETRY_INITIAL_DELAY_MS'] = '200'
        os.environ['RETRY_BACKOFF_MULTIPLIER'] = '3'
        os.environ['RETRY_MAX_DELAY_MS'] = '500'
        os.environ['RETRY_MAX_ATTEMPTS'] = '4'

        attempt_count = {'value': 0}
        retry_times = []

        @retry_with_backoff()
        def always_fail():
            attempt_count['value'] += 1
            retry_times.append(time.time())
            print(f"  Attempt {attempt_count['value']}")
            raise requests.exceptions.ConnectionError("Simulated connection error")

        try:
            always_fail()
        except requests.exceptions.ConnectionError:
            # Verify delay is capped at max_delay
            # Expected delays: 200ms, 500ms (capped from 600ms), 500ms (capped from 1800ms)
            if len(retry_times) >= 4:
                delay1_ms = (retry_times[1] - retry_times[0]) * 1000
                delay2_ms = (retry_times[2] - retry_times[1]) * 1000
                delay3_ms = (retry_times[3] - retry_times[2]) * 1000

                print(f"  Delay 1: {delay1_ms:.0f}ms (expected: ~200ms)")
                print(f"  Delay 2: {delay2_ms:.0f}ms (expected: ~500ms, capped)")
                print(f"  Delay 3: {delay3_ms:.0f}ms (expected: ~500ms, capped)")

                # Verify delay 2 and 3 are capped at max_delay (500ms)
                tolerance = 100
                self.assertLess(abs(delay2_ms - 500), tolerance,
                              f"Delay 2 should be capped at 500ms, got {delay2_ms:.0f}ms")
                self.assertLess(abs(delay3_ms - 500), tolerance,
                              f"Delay 3 should be capped at 500ms, got {delay3_ms:.0f}ms")

                print("  ✓ PASS: RETRY_MAX_DELAY_MS=500 correctly capped delays at 500ms")

    def test_all_env_vars_together(self):
        """Test that multiple environment variables work together."""
        print("\n=== Test 5: All Environment Variables Together ===")

        # Set all env vars
        os.environ['RETRY_MAX_ATTEMPTS'] = '2'
        os.environ['RETRY_INITIAL_DELAY_MS'] = '100'
        os.environ['RETRY_MAX_DELAY_MS'] = '200'
        os.environ['RETRY_BACKOFF_MULTIPLIER'] = '2'

        attempt_count = {'value': 0}
        retry_times = []

        @retry_with_backoff()
        def always_fail():
            attempt_count['value'] += 1
            retry_times.append(time.time())
            print(f"  Attempt {attempt_count['value']}")
            raise requests.exceptions.ConnectionError("Simulated connection error")

        try:
            always_fail()
        except requests.exceptions.ConnectionError:
            # Verify all settings applied
            self.assertEqual(attempt_count['value'], 2, "Should have 2 attempts")

            if len(retry_times) >= 2:
                delay_ms = (retry_times[1] - retry_times[0]) * 1000
                print(f"  Retry delay: {delay_ms:.0f}ms")

                # Should be ~100ms (initial delay)
                tolerance = 50
                diff = abs(delay_ms - 100)
                self.assertLess(diff, tolerance, f"Initial delay should be ~100ms, got {delay_ms:.0f}ms")

                print("  ✓ PASS: All environment variables work together correctly")


def run_tests():
    """Run all configuration verification tests."""
    print("=" * 60)
    print("Configuration Verification Tests")
    print("=" * 60)

    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(ConfigVerificationTest)

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    total = result.testsRun
    passed = total - len(result.failures) - len(result.errors)

    if result.wasSuccessful():
        print(f"\n✓ All {total} configuration tests passed!")
        print("\nAll environment variables work correctly:")
        print("  - RETRY_MAX_ATTEMPTS")
        print("  - RETRY_INITIAL_DELAY_MS")
        print("  - RETRY_MAX_DELAY_MS")
        print("  - RETRY_BACKOFF_MULTIPLIER")
        return 0
    else:
        print(f"\n✗ {len(result.failures) + len(result.errors)} out of {total} tests failed")
        return 1


if __name__ == '__main__':
    sys.exit(run_tests())
