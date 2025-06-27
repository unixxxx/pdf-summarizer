"""Retry logic and circuit breaker patterns for external services."""

from typing import Callable

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .logger import logger


class LLMError(Exception):
    """Base exception for LLM operations."""
    pass


class RateLimitError(Exception):
    """Rate limit exceeded error."""
    pass


class ExternalAPIError(Exception):
    """External API call failed."""
    pass


def retry_on_llm_error(max_attempts: int = 3) -> Callable:
    """
    Specialized retry decorator for LLM operations.
    
    Retries on:
    - LLMError
    - RateLimitError
    - Connection errors
    
    Args:
        max_attempts: Maximum number of retry attempts
        
    Returns:
        Decorated function with LLM-specific retry logic
    """
    def log_retry(retry_state):
        """Custom retry logging."""
        logger.warning(
            "Retrying LLM operation",
            retry_type="llm",
            attempt=retry_state.attempt_number,
            wait_time=retry_state.next_action.sleep if retry_state.next_action else 0,
            exception=str(retry_state.outcome.exception()) if retry_state.outcome else None
        )
    
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=2.0, min=2.0, max=30.0),
        retry=retry_if_exception_type((LLMError, RateLimitError, ConnectionError, TimeoutError)),
        before_sleep=log_retry,
        reraise=True,
    )


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
    
    def log_retry(retry_state):
        """Custom retry logging."""
        logger.warning(
            f"Retrying {service_name} API operation",
            retry_type=f"{service_name}_api",
            attempt=retry_state.attempt_number,
            wait_time=retry_state.next_action.sleep if retry_state.next_action else 0,
            exception=str(retry_state.outcome.exception()) if retry_state.outcome else None
        )
    
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=2.0, min=1.0, max=20.0),
        retry=retry_if_exception_type(tuple(exceptions)),
        before_sleep=log_retry,
        reraise=True,
    )