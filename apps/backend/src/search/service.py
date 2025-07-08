"""Fast, cost-effective search service without LLM dependencies.

This module provides the main search service for DocuLearn, implementing:
- Hybrid search combining vector, full-text, and fuzzy matching
- Local sentence-transformer reranking for improved relevance
- Redis caching for performance optimization
- Zero external API costs
"""

import logging
import re
import time
import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..common.cache_service import CacheService
from ..config import get_settings
from .reranker import SentenceTransformerReranker
from .schemas import QueryIntent, SearchMetrics, SearchQuery, SearchResult
from .search_engine import SearchEngine

logger = logging.getLogger(__name__)

# Global reranker instance to avoid reloading model
_global_reranker = None


class SearchService:
    """Production-grade search service optimized for speed and cost."""

    def __init__(self):
        """Initialize fast search components."""
        global _global_reranker

        self.search_engine = SearchEngine()

        # Initialize cache service
        settings = get_settings()
        self.cache_service = CacheService(settings)
        self.cache_ttl = settings.search_cache_ttl
        self.enable_reranking = settings.enable_reranking
        self.max_rerank_results = settings.max_rerank_results

        # Use global reranker instance
        if self.enable_reranking:
            if _global_reranker is None:
                try:
                    _global_reranker = SentenceTransformerReranker()
                    _global_reranker.preload_model()
                    logger.info(
                        "Initialized global sentence transformer model for reranking"
                    )
                except Exception as e:
                    logger.warning(f"Failed to initialize global reranker model: {e}")
                    self.enable_reranking = False
            self.reranker = _global_reranker
        else:
            self.reranker = None

    async def search(
        self, query: SearchQuery, db: AsyncSession
    ) -> tuple[list[SearchResult], SearchMetrics]:
        """
        Perform fast, cost-effective search.

        Args:
            query: Search query with parameters
            db: Database session

        Returns:
            Tuple of (results, metrics)
        """
        start_time = time.time()
        query_id = str(uuid.uuid4())

        metrics = SearchMetrics(
            query_id=query_id,
            total_time_ms=0,
            results_count=0
        )

        try:
            # Check cache if enabled
            if self.cache_service.enabled:
                cache_key = self._get_cache_key(query)
                logger.debug(f"Checking cache with key: {cache_key}")
                cached_results = await self._get_cached_results(query)
                if cached_results:
                    metrics.cache_hit = True
                    metrics.total_time_ms = (time.time() - start_time) * 1000
                    metrics.results_count = len(cached_results)
                    logger.info(
                        f"Cache hit for query: {query.query}, returned {len(cached_results)} results"
                    )
                    return cached_results, metrics
                else:
                    logger.debug(f"Cache miss for query: {query.query}")

            # Process query
            query_start = time.time()
            processed_query = self._process_query(query.query)
            query_processing_ms = (time.time() - query_start) * 1000
            logger.info(f"Query processed in {query_processing_ms:.2f}ms")

            # Perform hybrid search
            search_start = time.time()
            search_results, search_timing = await self.search_engine.search(
                query=processed_query.normalized_query,
                user_id=query.user_id,
                db=db,
                folder_id=query.folder_id,
                unfiled=query.unfiled,
                limit=self.max_rerank_results if self.enable_reranking else query.limit,
                offset=0 if self.enable_reranking else query.offset,
                min_score=query.min_relevance_score,
                include_archived=query.include_archived,
            )
            search_ms = (time.time() - search_start) * 1000
            logger.info(
                f"Search completed in {search_ms:.2f}ms with {len(search_results)} results"
            )

            metrics.vector_search_ms = search_timing.get("vector_search_ms", 0)
            metrics.fulltext_search_ms = search_timing.get("fulltext_search_ms", 0)

            # Rerank results if enabled and we have results
            if search_results and self.enable_reranking and self.reranker:
                rerank_start = time.time()
                try:
                    search_results = await self.reranker.rerank(
                        query.query,
                        search_results,
                        max_results=query.limit,
                        min_similarity=0.1,  # Lower threshold to allow fuzzy matches
                    )
                    metrics.rerank_time_ms = (time.time() - rerank_start) * 1000
                    logger.info(
                        f"Reranking completed in {metrics.rerank_time_ms:.2f}ms"
                    )
                except Exception as e:
                    logger.warning(f"Reranking failed, using original results: {e}")
                    # If reranking fails, just use original results
                    search_results = search_results[: query.limit]
            else:
                # No reranking, apply pagination
                if not self.enable_reranking:
                    search_results = search_results[
                        query.offset : query.offset + query.limit
                    ]

            # Calculate quality metrics
            if search_results:
                relevance_scores = [r.relevance_score for r in search_results]
                metrics.avg_relevance_score = sum(relevance_scores) / len(
                    relevance_scores
                )
                metrics.top_relevance_score = max(relevance_scores)

            # Update metrics
            metrics.results_count = len(search_results)
            metrics.total_time_ms = (time.time() - start_time) * 1000

            # Cache results if enabled
            if self.cache_service.enabled and search_results:
                logger.debug(
                    f"Caching {len(search_results)} results for query: {query.query}"
                )
                await self._cache_results(query, search_results)
            elif self.cache_service.enabled and not search_results:
                logger.debug(f"Not caching empty results for query: {query.query}")

            # Log search analytics
            logger.info(
                f"Fast search completed: {metrics.results_count} results in {metrics.total_time_ms:.2f}ms "
                f"(query: {query_processing_ms:.2f}ms, search: {search_ms:.2f}ms, "
                f"rerank: {metrics.rerank_time_ms:.2f}ms)"
            )

            return search_results, metrics

        except Exception as e:
            logger.error(f"Fast search failed for query '{query.query}': {e}")
            metrics.total_time_ms = (time.time() - start_time) * 1000
            return [], metrics

    async def _get_cached_results(
        self, query: SearchQuery
    ) -> list[SearchResult] | None:
        """Get cached search results."""
        try:
            cache_key = self._get_cache_key(query)
            cached_data = await self.cache_service.get(cache_key)

            logger.debug(f"Cache key: {cache_key}")
            logger.debug(
                f"Cached data type: {type(cached_data)}, length: {len(cached_data) if cached_data else 0}"
            )

            if cached_data:
                # Convert dict data back to SearchResult objects
                results = []
                for result_data in cached_data:
                    # Handle datetime conversion
                    if result_data.get("created_at"):
                        result_data["created_at"] = datetime.fromisoformat(
                            result_data["created_at"]
                        )

                    # Handle UUID conversion
                    if result_data.get("document_id"):
                        result_data["document_id"] = UUID(result_data["document_id"])

                    results.append(SearchResult(**result_data))

                return results

        except Exception as e:
            logger.error(f"Cache retrieval failed: {e}", exc_info=True)

        return None

    async def _cache_results(
        self, query: SearchQuery, results: list[SearchResult]
    ) -> None:
        """Cache search results."""
        # Don't cache empty results
        if not results:
            logger.debug("Not caching empty results")
            return

        try:
            cache_key = self._get_cache_key(query)

            # Convert results to serializable format
            results_data = [
                {
                    "document_id": str(r.document_id),
                    "filename": r.filename,
                    "title": r.title,
                    "snippet": r.snippet,
                    "relevance_score": r.relevance_score,
                    "vector_score": r.vector_score,
                    "fulltext_score": r.fulltext_score,
                    "rerank_score": r.rerank_score,
                    "matched_chunks": r.matched_chunks,
                    "explanation": r.explanation,
                    "tags": r.tags,
                    "folder_name": r.folder_name,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in results
            ]

            success = await self.cache_service.set(
                cache_key, results_data, ttl=self.cache_ttl
            )

            if success:
                logger.debug(
                    f"Successfully cached {len(results)} results with key: {cache_key}"
                )
            else:
                logger.warning(f"Failed to cache results with key: {cache_key}")

        except Exception as e:
            logger.error(f"Cache storage failed: {e}", exc_info=True)

    def _get_cache_key(self, query: SearchQuery) -> str:
        """Generate cache key for query."""
        # Include relevant parameters in cache key
        key_parts = [
            "fastsearch",
            str(query.user_id),
            query.query.lower(),
            str(query.folder_id) if query.folder_id else "all",
            str(query.unfiled),
            str(query.include_archived),
            str(query.limit),
            str(query.offset),
            str(self.enable_reranking),
        ]
        return ":".join(key_parts)
    
    def _process_query(self, query: str) -> QueryIntent:
        """Process query with simple, language-agnostic methods."""
        # Basic normalization
        normalized = self._normalize_query(query)
        
        # Extract quoted phrases for exact matching
        exact_phrases = re.findall(r'"([^"]+)"', query)
        
        # Remove quotes from normalized query
        normalized_no_quotes = re.sub(r'"[^"]+"', '', normalized).strip()
        
        # Simple tokenization
        tokens = normalized_no_quotes.split()
        
        return QueryIntent(
            original_query=query,
            normalized_query=normalized,
            key_terms=tokens[:10],  # Limit to prevent too many terms
            filters={"exact_phrases": exact_phrases} if exact_phrases else {},
            semantic_expansion=[],  # No expansion without domain knowledge
            confidence=0.9  # High confidence for simple processing
        )
    
    def _normalize_query(self, query: str) -> str:
        """Basic normalization that works for any language."""
        # Trim whitespace
        normalized = query.strip()
        
        # Collapse multiple spaces
        normalized = " ".join(normalized.split())
        
        # Convert to lowercase (works for most languages)
        normalized = normalized.lower()
        
        return normalized
