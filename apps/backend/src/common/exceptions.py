from typing import Any, Dict, Optional

from fastapi import HTTPException, status


class PDFSummarizerException(HTTPException):
    """Base exception for PDF Summarizer API."""

    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class PDFProcessingError(PDFSummarizerException):
    """Raised when PDF processing fails."""

    def __init__(self, detail: str = "Failed to process PDF file"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail
        )


class PDFTooLargeError(PDFSummarizerException):
    """Raised when PDF exceeds size limits."""

    def __init__(self, max_size_mb: int):
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"PDF file exceeds maximum size of {max_size_mb}MB",
        )


class PDFTooManyPagesError(PDFSummarizerException):
    """Raised when PDF has too many pages."""

    def __init__(self, max_pages: int):
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"PDF file exceeds maximum of {max_pages} pages",
        )


class InvalidFileTypeError(PDFSummarizerException):
    """Raised when uploaded file is not a PDF."""

    def __init__(self, file_type: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type: {file_type}. Only PDF files are allowed",
        )


class EmptyContentError(PDFSummarizerException):
    """Raised when no text content is found."""

    def __init__(self, source: str = "file"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No text content found in {source}",
        )


class SummarizationError(PDFSummarizerException):
    """Raised when summarization fails."""

    def __init__(self, detail: str = "Failed to generate summary"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail
        )


class OpenAIConfigError(PDFSummarizerException):
    """Raised when OpenAI is not properly configured."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenAI API is not configured. Please check API key settings",
        )


class ServiceUnavailableError(PDFSummarizerException):
    """Raised when a required service is unavailable."""

    def __init__(self, service: str):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{service} service is currently unavailable",
        )


class NotFoundError(PDFSummarizerException):
    """Raised when a resource is not found."""

    def __init__(self, resource: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} not found",
        )


class StorageError(PDFSummarizerException):
    """Raised when storage operations fail."""

    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Storage error: {detail}",
        )
