"""Worker exceptions."""


class WorkerError(Exception):
    """Base exception for worker errors."""
    pass


class EmbeddingError(WorkerError):
    """Exception raised when embedding generation fails."""
    pass


class ProcessingError(WorkerError):
    """Exception raised when document processing fails."""
    pass


class LLMError(WorkerError):
    """Exception raised for LLM-related errors."""
    pass