"""
Centralized error handling and utility decorators
"""

import logging
import functools
from typing import Callable, Any, Optional, TypeVar, List
from src.errors import MGL_AnalyticsException

logger = logging.getLogger(__name__)

T = TypeVar('T')


def safe_run(
    default_return: Any = None,
    log_level: str = "ERROR",
    raise_on_error: bool = False,
    retries: int = 0
) -> Callable:
    """
    Decorator for safe function execution with error handling.
    Catches exceptions, logs them, and returns default value.

    Args:
        default_return: Value to return on error
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        raise_on_error: If True, re-raise exceptions
        retries: Number of retry attempts

    Returns:
        Decorated function

    Example:
        @safe_run(default_return=[], log_level="WARNING")
        def fetch_data():
            return [1, 2, 3]
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            attempt = 0
            last_exception = None

            while attempt <= retries:
                try:
                    return func(*args, **kwargs)
                except MGL_AnalyticsException as e:
                    last_exception = e
                    log_msg = f"MGL Error in {func.__name__}: {str(e)}"
                except Exception as e:
                    last_exception = e
                    log_msg = f"Error in {func.__name__}: {str(e)[:100]}"

                attempt += 1

                if attempt <= retries:
                    log_msg += f" (Retry {attempt}/{retries})"
                    logger.warning(log_msg)
                else:
                    getattr(logger, log_level.lower())(log_msg)

            if raise_on_error and last_exception:
                raise last_exception

            return default_return

        return wrapper
    return decorator


def async_safe_run(
    default_return: Any = None,
    log_level: str = "ERROR",
    raise_on_error: bool = False,
    retries: int = 0
) -> Callable:
    """
    Async version of safe_run decorator.

    Args:
        default_return: Value to return on error
        log_level: Logging level
        raise_on_error: If True, re-raise exceptions
        retries: Number of retry attempts

    Returns:
        Decorated async function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            attempt = 0
            last_exception = None

            while attempt <= retries:
                try:
                    return await func(*args, **kwargs)
                except MGL_AnalyticsException as e:
                    last_exception = e
                    log_msg = f"MGL Error in {func.__name__}: {str(e)}"
                except Exception as e:
                    last_exception = e
                    log_msg = f"Error in {func.__name__}: {str(e)[:100]}"

                attempt += 1

                if attempt <= retries:
                    log_msg += f" (Retry {attempt}/{retries})"
                    logger.warning(log_msg)
                else:
                    getattr(logger, log_level.lower())(log_msg)

            if raise_on_error and last_exception:
                raise last_exception

            return default_return

        return wrapper
    return decorator


def rate_limit(calls: int = 50, period: int = 1) -> Callable:
    """
    Rate limiting decorator (token bucket algorithm).

    Args:
        calls: Number of calls allowed
        period: Time period in seconds

    Returns:
        Decorated function
    """
    import time
    import threading

    lock = threading.Lock()
    min_interval = period / calls
    last_called = [0.0]

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            with lock:
                elapsed = time.time() - last_called[0]
                if elapsed < min_interval:
                    time.sleep(min_interval - elapsed)
                last_called[0] = time.time()

            return func(*args, **kwargs)

        return wrapper
    return decorator


def cache_result(ttl: int = 300) -> Callable:
    """
    Simple caching decorator with TTL (time-to-live).

    Args:
        ttl: Time-to-live in seconds

    Returns:
        Decorated function
    """
    import time

    def decorator(func: Callable) -> Callable:
        cache = {}
        cache_time = {}

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            key = (args, tuple(sorted(kwargs.items())))
            now = time.time()

            if key in cache:
                if now - cache_time[key] < ttl:
                    return cache[key]

            result = func(*args, **kwargs)
            cache[key] = result
            cache_time[key] = now
            return result

        return wrapper
    return decorator
