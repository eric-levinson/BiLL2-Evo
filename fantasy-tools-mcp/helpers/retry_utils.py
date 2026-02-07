"""
Retry utilities with exponential backoff for Sleeper API calls.

Uses tenacity library for robust retry logic with rate-limit awareness.
"""

import os
import logging
from typing import Callable, Any, Optional
from functools import wraps

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    RetryError,
)
import requests

# Configure logging
logger = logging.getLogger(__name__)


def is_retryable_http_error(exception: Exception) -> bool:
    """
    Determine if an HTTP error should trigger a retry.

    Retries on:
    - 5xx server errors (temporary server issues)
    - 429 rate limit (should retry with backoff)
    - Connection errors (network issues)
    - Timeout errors

    Does NOT retry on:
    - 4xx client errors (except 429) - these won't succeed on retry

    Args:
        exception: The exception to check

    Returns:
        True if the error should trigger a retry
    """
    # Connection and timeout errors are always retryable
    if isinstance(exception, (requests.exceptions.ConnectionError,
                             requests.exceptions.Timeout)):
        return True

    # Check HTTP errors by status code
    if isinstance(exception, requests.exceptions.HTTPError):
        if hasattr(exception, 'response') and exception.response is not None:
            status_code = exception.response.status_code
            # Retry on 5xx (server errors) and 429 (rate limit)
            return status_code >= 500 or status_code == 429

    return False


def get_retry_after_delay(exception: Exception) -> Optional[float]:
    """
    Extract Retry-After header value from rate-limited response.

    The Retry-After header indicates how long to wait before retrying.
    It can be in seconds (integer) or an HTTP date string.

    Args:
        exception: HTTPError exception with response

    Returns:
        Delay in seconds if Retry-After header present, None otherwise
    """
    if isinstance(exception, requests.exceptions.HTTPError):
        if hasattr(exception, 'response') and exception.response is not None:
            response = exception.response
            if response.status_code == 429:
                retry_after = response.headers.get('Retry-After')
                if retry_after:
                    try:
                        # Try parsing as integer (seconds)
                        return float(retry_after)
                    except ValueError:
                        # If it's an HTTP date, we'd need to parse it
                        # For simplicity, fall back to default backoff
                        logger.warning(
                            f"Could not parse Retry-After header: {retry_after}"
                        )
    return None


def retry_with_backoff(
    max_attempts: Optional[int] = None,
    initial_delay: Optional[float] = None,
    max_delay: Optional[float] = None,
    multiplier: Optional[float] = None,
) -> Callable:
    """
    Decorator that adds retry logic with exponential backoff to a function.

    Default behavior (configurable via environment variables):
    - Attempt 1: Executes immediately
    - Attempt 2: Retries after 1s delay
    - Attempt 3: Retries after 2s delay
    - Attempt 4: Retries after 4s delay (if max_attempts=4)

    Retries on:
    - requests.exceptions.HTTPError (5xx and 429 only)
    - requests.exceptions.ConnectionError
    - requests.exceptions.Timeout

    Rate-limit handling:
    - Detects 429 responses
    - Respects Retry-After header if present
    - Falls back to exponential backoff

    Environment variables (with defaults):
    - RETRY_MAX_ATTEMPTS: Maximum retry attempts (default: 3)
    - RETRY_INITIAL_DELAY_MS: Initial delay in milliseconds (default: 1000)
    - RETRY_MAX_DELAY_MS: Maximum delay in milliseconds (default: 4000)
    - RETRY_BACKOFF_MULTIPLIER: Exponential backoff multiplier (default: 2)

    Args:
        max_attempts: Override for maximum retry attempts
        initial_delay: Override for initial delay in seconds
        max_delay: Override for maximum delay in seconds
        multiplier: Override for backoff multiplier

    Returns:
        Decorated function with retry logic

    Example:
        ```python
        @retry_with_backoff(max_attempts=3)
        def fetch_sleeper_data(url: str):
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        ```
    """
    # Read configuration from environment with fallbacks
    _max_attempts = max_attempts or int(os.getenv('RETRY_MAX_ATTEMPTS', '3'))
    _initial_delay_ms = initial_delay or int(os.getenv('RETRY_INITIAL_DELAY_MS', '1000'))
    _max_delay_ms = max_delay or int(os.getenv('RETRY_MAX_DELAY_MS', '4000'))
    _multiplier = multiplier or float(os.getenv('RETRY_BACKOFF_MULTIPLIER', '2'))

    # Convert milliseconds to seconds for tenacity
    _initial_delay_s = _initial_delay_ms / 1000.0
    _max_delay_s = _max_delay_ms / 1000.0

    def decorator(func: Callable) -> Callable:
        # Apply tenacity retry decorator
        retrying_func = retry(
            # Stop after max attempts
            stop=stop_after_attempt(_max_attempts),

            # Exponential backoff: wait = multiplier^(attempt-1) * initial_delay
            # Clamped between initial_delay and max_delay
            wait=wait_exponential(
                multiplier=_initial_delay_s,
                min=_initial_delay_s,
                max=_max_delay_s,
                exp_base=_multiplier,
            ),

            # Only retry on specific exceptions
            retry=retry_if_exception_type((
                requests.exceptions.HTTPError,
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
            )),

            # Log before sleeping (retrying)
            before_sleep=before_sleep_log(logger, logging.WARNING),

            # Custom retry condition
            retry_error_callback=lambda retry_state: is_retryable_http_error(
                retry_state.outcome.exception()
            ) if retry_state.outcome and retry_state.outcome.failed else False,
        )(func)

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return retrying_func(*args, **kwargs)
            except RetryError as e:
                # Extract the original exception from RetryError
                original_exception = e.last_attempt.exception()
                logger.error(
                    f"All {_max_attempts} retry attempts exhausted for {func.__name__}. "
                    f"Last error: {original_exception}"
                )
                # Re-raise the original exception instead of RetryError
                raise original_exception from e

        return wrapper

    return decorator
