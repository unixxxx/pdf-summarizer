"""Search models and data structures."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


@dataclass
class SearchWeights:
    """Configurable weights for different search components."""
    
    # Hybrid search weights
    vector_weight: float = 0.5
    fulltext_weight: float = 0.3
    # Note: fuzzy_weight is configured in settings.py (default 0.4)
    # The three weights don't need to sum to 1.0 as scores are relative


@dataclass
class QueryIntent:
    """Parsed query intent from query processor."""
    
    original_query: str
    normalized_query: str
    key_terms: list[str]
    filters: dict[str, Any]
    semantic_expansion: list[str]
    confidence: float


class SearchQuery(BaseModel):
    """Enhanced search query with metadata."""
    
    query: str = Field(..., min_length=1, description="Search query text")
    user_id: UUID
    folder_id: UUID | None = None
    unfiled: bool = False
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)
    
    # Advanced options
    include_archived: bool = False
    min_relevance_score: float = 0.1  # Lowered to allow fuzzy matches
    
    # Filters
    tags: list[str] = Field(default_factory=list, description="Filter by tags")
    file_types: list[str] = Field(default_factory=list, description="Filter by file extensions")
    date_range: str | None = Field(None, description="Date range filter")
    status: str | None = Field(None, description="Document status filter")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "machine learning papers about transformers",
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "limit": 20
            }
        }


@dataclass
class SearchResult:
    """Individual search result with scoring."""
    
    document_id: UUID
    filename: str
    title: str | None
    snippet: str
    relevance_score: float
    
    # Score breakdown
    vector_score: float = 0.0
    fulltext_score: float = 0.0
    rerank_score: float = 0.0
    
    # Metadata
    matched_chunks: list[dict[str, Any]] = None
    explanation: str | None = None
    tags: list[str] = None
    folder_name: str | None = None
    created_at: datetime | None = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.matched_chunks is None:
            self.matched_chunks = []
        if self.tags is None:
            self.tags = []


class SearchMetrics(BaseModel):
    """Search performance metrics."""
    
    query_id: str
    total_time_ms: float
    vector_search_ms: float = 0.0
    fulltext_search_ms: float = 0.0
    rerank_time_ms: float = 0.0
    
    results_count: int
    cache_hit: bool = False
    
    # Quality metrics
    avg_relevance_score: float = 0.0
    top_relevance_score: float = 0.0


