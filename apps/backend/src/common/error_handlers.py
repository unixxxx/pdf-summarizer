"""Common error handlers for consistent error responses."""

import logging
from functools import wraps
from typing import Callable

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from .exceptions import (
    DuplicateResourceError,
    NotFoundError,
    PDFProcessingError,
    PDFSummarizerException,
    ServiceUnavailableError,
    StorageError,
    SummarizationError,
)

logger = logging.getLogger(__name__)


def handle_errors(func: Callable) -> Callable:
    """
    Decorator to handle common exceptions and convert them to HTTP responses.
    
    This ensures consistent error handling across all endpoints.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except NotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        except DuplicateResourceError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            )
        except ServiceUnavailableError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(e),
            )
        except (SummarizationError, PDFProcessingError, StorageError) as e:
            logger.error(f"Processing error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e),
            )
        except PDFSummarizerException as e:
            # Re-raise as is - it's already an HTTPException
            raise e
        except IntegrityError as e:
            logger.error(f"Database integrity error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Database constraint violation",
            )
        except Exception:
            logger.exception(f"Unexpected error in {func.__name__}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred",
            )
    
    return wrapper