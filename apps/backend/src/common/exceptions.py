from typing import Any

from fastapi import HTTPException, status


class DocuLearnException(HTTPException):
    """Base exception for DocuLearn API."""

    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: dict[str, Any] | None = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)




class SummarizationError(DocuLearnException):
    """Raised when summarization fails."""

    def __init__(self, detail: str = "Failed to generate summary"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail
        )


class OpenAIConfigError(DocuLearnException):
    """Raised when OpenAI is not properly configured."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenAI API is not configured. Please check API key settings",
        )


class ServiceUnavailableError(DocuLearnException):
    """Raised when a required service is unavailable."""

    def __init__(self, service: str):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{service} service is currently unavailable",
        )


class StorageError(DocuLearnException):
    """Raised when storage operations fail."""

    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Storage error: {detail}",
        )




class BadRequestException(DocuLearnException):
    """Raised when request is invalid."""

    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class ConflictException(DocuLearnException):
    """Raised when there's a conflict with existing resource."""

    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )


class NotFoundException(DocuLearnException):
    """Raised when a resource is not found."""

    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )


# Database-related exceptions
class DatabaseError(DocuLearnException):
    """Base class for database-related errors."""

    def __init__(self, detail: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        super().__init__(status_code=status_code, detail=f"Database error: {detail}")




# External API exceptions
class ExternalAPIError(DocuLearnException):
    """Base class for external API errors."""

    def __init__(self, service: str, detail: str, status_code: int = status.HTTP_502_BAD_GATEWAY):
        super().__init__(
            status_code=status_code,
            detail=f"{service} API error: {detail}"
        )


class LLMError(ExternalAPIError):
    """Raised when LLM API calls fail."""

    def __init__(self, detail: str, provider: str | None = None):
        service = f"LLM ({provider})" if provider else "LLM"
        super().__init__(service=service, detail=detail)


class EmbeddingError(ExternalAPIError):
    """Raised when embedding generation fails."""

    def __init__(self, detail: str):
        super().__init__(service="Embedding", detail=detail)


class OAuthError(ExternalAPIError):
    """Raised when OAuth authentication fails."""

    def __init__(self, provider: str, detail: str):
        super().__init__(
            service=f"OAuth ({provider})",
            detail=detail,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


# Rate limiting and quota exceptions
class RateLimitError(DocuLearnException):
    """Raised when rate limit is exceeded."""

    def __init__(self, retry_after: int | None = None):
        headers = {"Retry-After": str(retry_after)} if retry_after else None
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers=headers
        )




# Validation exceptions
class ValidationError(DocuLearnException):
    """Raised when input validation fails."""

    def __init__(self, field: str, detail: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error for field '{field}': {detail}"
        )


