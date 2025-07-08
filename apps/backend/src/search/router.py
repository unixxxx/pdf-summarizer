"""Search API endpoints."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import get_current_user
from ..database.session import get_async_db
from .dependencies import get_search_service
from .schemas import SearchMetrics, SearchQuery, SearchResult
from .service import SearchService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/", response_model=tuple[list[SearchResult], SearchMetrics])
async def search_documents(
    query: SearchQuery,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
    search_service: Annotated[SearchService, Depends(get_search_service)]
) -> tuple[list[SearchResult], SearchMetrics]:
    """
    Search documents with hybrid search.
    
    Features:
    - Vector similarity search
    - Full-text search
    - Fuzzy matching for typo tolerance
    - Semantic reranking
    - Result caching
    """
    try:
        # Ensure user can only search their own documents
        query.user_id = current_user["id"]
        
        # Perform search
        results, metrics = await search_service.search(query, db)
        
        return results, metrics
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail="Search failed")


@router.get("/suggest")
async def search_suggestions(
    q: Annotated[str, Query(min_length=2, description="Search query")],
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[dict, Depends(get_current_user)]
) -> dict[str, list[str]]:
    """
    Get search suggestions based on partial query.
    
    Note: This is a placeholder. Real implementation would provide
    suggestions based on user's document content and search history.
    """
    # For now, just return empty suggestions
    return {
        "suggestions": [],
        "recent_searches": []
    }