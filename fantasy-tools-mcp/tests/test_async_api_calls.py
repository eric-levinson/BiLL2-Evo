"""
Test suite for async API calls with parallel execution.

Tests:
1. Async retry decorator behavior
2. Async _call_async method functionality
3. Parallel execution with asyncio.gather
4. Error handling and retry logic in async context
5. Performance improvements from parallel execution
"""

import asyncio
import logging
import os
import sys
import time
from unittest.mock import Mock, patch

import aiohttp
import pytest

# Configure pytest-asyncio to use 'auto' mode
pytest_plugins = ("pytest_asyncio",)

# Add parent directory to path so we can import from fantasy-tools-mcp root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from helpers.retry_utils import async_retry_with_backoff, is_retryable_http_error  # noqa: E402
from tools.fantasy.sleeper_wrapper.base_api import BaseApi  # noqa: E402

# Configure logging to see retry messages
logging.basicConfig(level=logging.WARNING, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


class TestAsyncRetryDecorator:
    """Test suite for async_retry_with_backoff decorator."""

    @pytest.mark.asyncio
    async def test_retry_behavior_with_exponential_backoff(self):
        """Test async retry behavior with exponential backoff using requests-compatible exceptions."""
        print("\n" + "=" * 70)
        print("TEST 1: Async Retry Behavior with Exponential Backoff")
        print("=" * 70)

        # Import requests to use its exception types (current retry logic expects these)
        import requests

        call_count = 0
        call_times = []

        @async_retry_with_backoff(max_attempts=3, initial_delay=0.1, max_delay=0.4, multiplier=2.0)
        async def failing_async_function():
            nonlocal call_count
            call_count += 1
            call_times.append(time.time())
            print(f"  Attempt {call_count} at {time.strftime('%H:%M:%S')}")

            # Use requests.ConnectionError which is recognized by is_retryable_http_error
            raise requests.exceptions.ConnectionError("Connection failed")

        start_time = time.time()

        # Execute the async function and expect it to fail after retries
        try:
            await failing_async_function()
            raise AssertionError("Should have raised ConnectionError")
        except requests.exceptions.ConnectionError:
            elapsed = time.time() - start_time
            print(f"\n✓ All {call_count} attempts completed in {elapsed:.2f}s")
            print("  Expected: ~3 attempts in ~0.3s (0.1s + 0.2s delays)")

            # Verify attempt count
            assert call_count == 3, f"Expected 3 attempts, got {call_count}"
            print(f"✓ Attempt count: {call_count} (correct)")

            # Verify timing (allow tolerance for async operations)
            if len(call_times) >= 3:
                delay1 = call_times[1] - call_times[0]
                delay2 = call_times[2] - call_times[1]

                print(f"✓ Delay 1: {delay1:.3f}s (expected ~0.1s)")
                print(f"✓ Delay 2: {delay2:.3f}s (expected ~0.2s)")

                # Verify delays are approximately correct (within 100ms tolerance for async)
                assert 0.05 <= delay1 <= 0.25, f"Delay 1 out of range: {delay1}"
                assert 0.15 <= delay2 <= 0.35, f"Delay 2 out of range: {delay2}"

            print("\n✅ TEST PASSED: Async retry behavior working correctly")

    @pytest.mark.asyncio
    async def test_rate_limit_handling(self):
        """Test rate-limit handling with 429 responses in async context."""
        print("\n" + "=" * 70)
        print("TEST 2: Async Rate-Limit Handling (429 Responses)")
        print("=" * 70)

        import requests

        call_count = 0

        @async_retry_with_backoff(max_attempts=3, initial_delay=0.05, max_delay=0.2)
        async def rate_limited_async_function():
            nonlocal call_count
            call_count += 1
            print(f"  Attempt {call_count} at {time.strftime('%H:%M:%S')}")

            # Use requests.HTTPError with 429 status (recognized by retry logic)
            response = Mock()
            response.status_code = 429
            response.headers = {"Retry-After": "1"}

            error = requests.exceptions.HTTPError()
            error.response = response
            raise error

        try:
            await rate_limited_async_function()
            raise AssertionError("Should have raised HTTPError")
        except requests.exceptions.HTTPError:
            print(f"\n✓ All {call_count} attempts completed")
            assert call_count == 3, f"Expected 3 attempts, got {call_count}"
            print(f"✓ Attempt count: {call_count} (correct)")
            print("✓ 429 errors trigger retries as expected")

            print("\n✅ TEST PASSED: Async rate-limit handling working correctly")

    @pytest.mark.asyncio
    async def test_successful_retry_after_failures(self):
        """Test that function succeeds on retry after initial failures."""
        print("\n" + "=" * 70)
        print("TEST 3: Successful Retry After Failures")
        print("=" * 70)

        import requests

        call_count = 0

        @async_retry_with_backoff(max_attempts=3, initial_delay=0.05, max_delay=0.2)
        async def eventually_succeeds():
            nonlocal call_count
            call_count += 1
            print(f"  Attempt {call_count}")

            # Fail on first two attempts, succeed on third
            if call_count < 3:
                raise requests.exceptions.ConnectionError("Connection failed")

            return {"success": True, "data": "test"}

        result = await eventually_succeeds()

        print(f"\n✓ Function succeeded after {call_count} attempts")
        assert call_count == 3, f"Expected 3 attempts, got {call_count}"
        assert result == {"success": True, "data": "test"}
        print("✓ Return value correct")

        print("\n✅ TEST PASSED: Retry succeeds after failures")


class TestAsyncCallMethod:
    """Test suite for BaseApi._call_async method."""

    @pytest.mark.asyncio
    async def test_call_async_basic_functionality(self):
        """Test basic _call_async functionality with mocked aiohttp."""
        print("\n" + "=" * 70)
        print("TEST 4: BaseApi._call_async Basic Functionality")
        print("=" * 70)

        api = BaseApi()

        # Mock the aiohttp session and response
        mock_response_data = {"user_id": "12345", "username": "test_user"}

        class MockResponse:
            def __init__(self):
                self.status = 200

            async def json(self):
                return mock_response_data

            def raise_for_status(self):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

        class MockSession:
            def __init__(self):
                self.get_call_count = 0

            def get(self, url):
                self.get_call_count += 1
                return MockResponse()

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

        mock_session = MockSession()

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await api._call_async("https://api.sleeper.app/v1/user/test")

            print(f"  API call result: {result}")
            assert result == mock_response_data
            print("✓ Response data correct")

            # Verify session.get was called
            assert mock_session.get_call_count == 1
            print("✓ HTTP GET called")

            print("\n✅ TEST PASSED: _call_async basic functionality working")

    @pytest.mark.asyncio
    async def test_call_async_retry_on_error(self):
        """Test that _call_async retries on network errors."""
        print("\n" + "=" * 70)
        print("TEST 5: _call_async Retry on Network Errors")
        print("=" * 70)

        import requests

        api = BaseApi()

        class MockResponse:
            def __init__(self):
                self.status = 200

            async def json(self):
                return {"success": True}

            def raise_for_status(self):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

        class MockSession:
            def __init__(self):
                self.call_count = 0

            def get(self, url):
                self.call_count += 1
                print(f"  Mock API call attempt {self.call_count}")

                # Fail first 2 attempts with requests.ConnectionError, succeed on 3rd
                if self.call_count < 3:
                    raise requests.exceptions.ConnectionError("Connection failed")

                # Success on 3rd attempt
                return MockResponse()

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

        mock_session = MockSession()

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await api._call_async("https://api.sleeper.app/v1/user/test")

            print(f"\n✓ API call succeeded after {mock_session.call_count} attempts")
            assert mock_session.call_count == 3, f"Expected 3 attempts, got {mock_session.call_count}"
            assert result == {"success": True}
            print("✓ Retry decorator working with _call_async")

            print("\n✅ TEST PASSED: _call_async retries correctly on errors")


class TestParallelExecution:
    """Test suite for parallel execution with asyncio.gather."""

    @pytest.mark.asyncio
    async def test_parallel_execution_faster_than_sequential(self):
        """Test that parallel execution is faster than sequential."""
        print("\n" + "=" * 70)
        print("TEST 6: Parallel Execution Performance")
        print("=" * 70)

        # Simulate API calls with 100ms delay each
        async def mock_api_call(endpoint: str, delay: float = 0.1):
            """Mock async API call with configurable delay."""
            await asyncio.sleep(delay)
            return {"endpoint": endpoint, "data": "success"}

        # Sequential execution
        start_seq = time.time()
        await mock_api_call("endpoint1")
        await mock_api_call("endpoint2")
        await mock_api_call("endpoint3")
        sequential_time = time.time() - start_seq

        # Parallel execution
        start_par = time.time()
        results = await asyncio.gather(
            mock_api_call("endpoint1"), mock_api_call("endpoint2"), mock_api_call("endpoint3")
        )
        parallel_time = time.time() - start_par

        print(f"\n  Sequential execution: {sequential_time:.3f}s")
        print(f"  Parallel execution:   {parallel_time:.3f}s")
        print(f"  Speedup:              {sequential_time / parallel_time:.2f}x")

        # Verify parallel is significantly faster (at least 2x for 3 calls)
        assert parallel_time < sequential_time / 2, "Parallel execution should be at least 2x faster"
        print("✓ Parallel execution is significantly faster")

        # Verify all results are correct
        assert len(results) == 3
        assert all(r["data"] == "success" for r in results)
        print("✓ All parallel results correct")

        print("\n✅ TEST PASSED: Parallel execution performance verified")

    @pytest.mark.asyncio
    async def test_parallel_execution_error_handling(self):
        """Test error handling in parallel execution with asyncio.gather."""
        print("\n" + "=" * 70)
        print("TEST 7: Parallel Execution Error Handling")
        print("=" * 70)

        async def successful_call():
            await asyncio.sleep(0.05)
            return {"status": "success"}

        async def failing_call():
            await asyncio.sleep(0.05)
            raise ValueError("Simulated error")

        # Test that gather propagates exceptions
        try:
            results = await asyncio.gather(successful_call(), failing_call(), successful_call())
            raise AssertionError("Should have raised ValueError")
        except ValueError as e:
            print(f"  ✓ Exception propagated from gather: {e}")
            print("✓ Error handling working correctly")

        # Test gather with return_exceptions=True
        results = await asyncio.gather(successful_call(), failing_call(), successful_call(), return_exceptions=True)

        print(f"\n  Results with return_exceptions=True: {len(results)} items")
        assert len(results) == 3
        assert results[0] == {"status": "success"}
        assert isinstance(results[1], ValueError)
        assert results[2] == {"status": "success"}
        print("✓ return_exceptions=True allows partial success")

        print("\n✅ TEST PASSED: Parallel execution error handling verified")

    @pytest.mark.asyncio
    async def test_base_api_parallel_calls(self):
        """Test parallel execution using BaseApi._call_async."""
        print("\n" + "=" * 70)
        print("TEST 8: BaseApi Parallel Execution")
        print("=" * 70)

        api = BaseApi()

        # Mock responses for three different endpoints
        mock_responses = [
            {"endpoint": "endpoint1", "data": "response1"},
            {"endpoint": "endpoint2", "data": "response2"},
            {"endpoint": "endpoint3", "data": "response3"},
        ]

        class MockResponse:
            def __init__(self, response_data):
                self.status = 200
                self.response_data = response_data

            async def json(self):
                return self.response_data

            def raise_for_status(self):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

        class MockSession:
            def __init__(self):
                self.call_count = 0
                self.call_times = []

            def get(self, url):
                self.call_count += 1
                self.call_times.append(time.time())

                # Return different response based on URL
                idx = int(url.split("endpoint")[1]) - 1

                # Create a MockResponse that simulates async delay
                class DelayedMockResponse(MockResponse):
                    def __init__(self, response_data):
                        super().__init__(response_data)

                    async def __aenter__(self):
                        # Simulate 50ms API delay
                        await asyncio.sleep(0.05)
                        return self

                return DelayedMockResponse(mock_responses[idx])

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

        mock_session = MockSession()

        with patch("aiohttp.ClientSession", return_value=mock_session):
            start_time = time.time()

            # Execute three API calls in parallel
            results = await asyncio.gather(
                api._call_async("https://api.sleeper.app/v1/endpoint1"),
                api._call_async("https://api.sleeper.app/v1/endpoint2"),
                api._call_async("https://api.sleeper.app/v1/endpoint3"),
            )

            total_time = time.time() - start_time

            print(f"\n  Total execution time: {total_time:.3f}s")
            print("  Expected time: ~0.05s (parallel) vs ~0.15s (sequential)")

            # Verify all calls were made
            assert mock_session.call_count == 3, f"Expected 3 calls, got {mock_session.call_count}"
            print(f"✓ Made {mock_session.call_count} API calls")

            # Verify parallel execution (should be close to 50ms, not 150ms)
            # Allow some tolerance for async overhead
            assert total_time < 0.20, f"Parallel execution too slow: {total_time:.3f}s"
            print("✓ Execution time indicates parallel processing")

            # Verify all results are correct
            assert len(results) == 3
            for i, result in enumerate(results):
                assert result == mock_responses[i]
            print("✓ All results correct")

            print("\n✅ TEST PASSED: BaseApi parallel execution verified")


class TestHelperFunctions:
    """Test helper functions used in async retry logic."""

    def test_is_retryable_http_error_with_aiohttp_errors(self):
        """Test is_retryable_http_error with aiohttp exception types."""
        print("\n" + "=" * 70)
        print("TEST 9: Helper Functions with aiohttp Errors")
        print("=" * 70)

        # Note: is_retryable_http_error now handles both requests and aiohttp exceptions
        # This test verifies both libraries are properly supported

        # Test with requests exceptions
        import requests

        conn_error = requests.exceptions.ConnectionError()
        assert is_retryable_http_error(conn_error), "ConnectionError should be retryable"
        print("  ✓ requests.ConnectionError is retryable")

        timeout_error = requests.exceptions.Timeout()
        assert is_retryable_http_error(timeout_error), "Timeout should be retryable"
        print("  ✓ requests.Timeout is retryable")

        # 5xx should be retryable
        response_5xx = Mock()
        response_5xx.status_code = 503
        error_5xx = requests.exceptions.HTTPError()
        error_5xx.response = response_5xx
        assert is_retryable_http_error(error_5xx), "5xx should be retryable"
        print("  ✓ 5xx errors are retryable")

        # 429 should be retryable
        response_429 = Mock()
        response_429.status_code = 429
        error_429 = requests.exceptions.HTTPError()
        error_429.response = response_429
        assert is_retryable_http_error(error_429), "429 should be retryable"
        print("  ✓ 429 errors are retryable")

        # Test with aiohttp exceptions (new implementation)

        # aiohttp.ClientConnectionError should be retryable
        conn_error_aiohttp = aiohttp.ClientConnectionError()
        assert is_retryable_http_error(conn_error_aiohttp), "aiohttp.ClientConnectionError should be retryable"
        print("  ✓ aiohttp.ClientConnectionError is retryable")

        # aiohttp.ClientError (non-response) should be retryable
        client_error_aiohttp = aiohttp.ClientError()
        assert is_retryable_http_error(client_error_aiohttp), "aiohttp.ClientError should be retryable"
        print("  ✓ aiohttp.ClientError is retryable")

        # aiohttp.ClientResponseError with 429 should be retryable
        error_429_aiohttp = aiohttp.ClientResponseError(
            request_info=Mock(), history=(), status=429, message="Too Many Requests"
        )
        assert is_retryable_http_error(error_429_aiohttp), "aiohttp.ClientResponseError with 429 should be retryable"
        print("  ✓ aiohttp.ClientResponseError with 429 is retryable")

        # aiohttp.ClientResponseError with 503 should be retryable
        error_503_aiohttp = aiohttp.ClientResponseError(
            request_info=Mock(), history=(), status=503, message="Service Unavailable"
        )
        assert is_retryable_http_error(error_503_aiohttp), "aiohttp.ClientResponseError with 503 should be retryable"
        print("  ✓ aiohttp.ClientResponseError with 503 is retryable")

        # aiohttp.ClientResponseError with 404 should NOT be retryable
        error_404_aiohttp = aiohttp.ClientResponseError(
            request_info=Mock(), history=(), status=404, message="Not Found"
        )
        assert not is_retryable_http_error(error_404_aiohttp), (
            "aiohttp.ClientResponseError with 404 should NOT be retryable"
        )
        print("  ✓ aiohttp.ClientResponseError with 404 is NOT retryable")

        print("\n✅ TEST PASSED: Helper functions verified (requests + aiohttp)")


def run_all_tests():
    """Run all tests using pytest."""
    print("\n" + "=" * 70)
    print("ASYNC API CALL TEST SUITE")
    print("=" * 70)
    print("\nThis test suite verifies:")
    print("  1. Async retry decorator with exponential backoff")
    print("  2. Async _call_async method functionality")
    print("  3. Parallel execution with asyncio.gather")
    print("  4. Error handling in async context")
    print("  5. Performance improvements from parallelization")
    print("\nRunning tests with pytest...")

    # Run pytest programmatically
    import pytest

    return pytest.main([__file__, "-v", "-s"])


if __name__ == "__main__":
    sys.exit(run_all_tests())
