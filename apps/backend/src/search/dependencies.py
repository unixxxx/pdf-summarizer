"""Search service dependencies for FastAPI dependency injection."""

from typing import Annotated

from fastapi import Depends, Request

from .service import SearchService


def get_search_service(request: Request) -> SearchService:
    """
    Get search service from app state.
    
    This dependency ensures we use the pre-initialized search service
    that was created during application startup.
    """
    if hasattr(request.app.state, "search_service"):
        return request.app.state.search_service
    
    # Fallback: create new instance if not in app state
    # This shouldn't happen in normal operation but provides safety
    return SearchService()


# Type alias for dependency injection
SearchServiceDep = Annotated[SearchService, Depends(get_search_service)]