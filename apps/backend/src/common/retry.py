"""Retry logic and circuit breaker patterns for external services."""

import logging
from typing import Callable

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from tenacity.before_sleep import before_sleep_log

from .exceptions import ExternalAPIError, RateLimitError

logger = logging.getLogger(__name__)




def retry_on_external_api(
    service_name: str,
    max_attempts: int = 3,
    include_rate_limit: bool = True,
) -> Callable:
    """
    Retry decorator for external API calls.
    
    Args:
        service_name: Name of the external service for logging
        max_attempts: Maximum number of retry attempts
        include_rate_limit: Whether to retry on rate limit errors
        
    Returns:
        Decorated function with external API retry logic
    """
    exceptions = [ExternalAPIError, ConnectionError, TimeoutError]
    if include_rate_limit:
        exceptions.append(RateLimitError)
    
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=2.0, min=1.0, max=20.0),
        retry=retry_if_exception_type(tuple(exceptions)),
        before_sleep=before_sleep_log(logger.getChild(f"{service_name}_retry"), logging.WARNING),
        reraise=True,
    )
