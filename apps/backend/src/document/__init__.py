"""Document domain module."""

from .dependencies import DocumentServiceDep
from .router import router
from .schemas import DocumentResponse, LibraryItemResponse, PaginatedLibraryResponse
from .service import DocumentService

__all__ = [
    "router",
    "DocumentService",
    "DocumentServiceDep",
    "DocumentResponse",
    "LibraryItemResponse",
    "PaginatedLibraryResponse",
]