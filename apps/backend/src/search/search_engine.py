"""Hybrid search engine combining multiple search strategies.

This module implements the core search functionality:
- Vector similarity search using pgvector embeddings
- Full-text search using PostgreSQL tsvector
- Fuzzy search using trigram similarity for typo tolerance
- Weighted scoring combining all three approaches
"""

import logging
import time
from uuid import UUID

from shared.models import Document, DocumentChunk
from sqlalchemy import Float, and_, cast, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..common.embeddings_service import get_embedding_service
from ..config import get_settings
from .schemas import SearchResult, SearchWeights

logger = logging.getLogger(__name__)


class SearchEngine:
    """Search engine combining vector and full-text search (hybrid search)."""
    
    def __init__(self, weights: SearchWeights | None = None):
        """Initialize search engine."""
        self.embedding_service = None
        self.weights = weights or SearchWeights()
        self.settings = get_settings()
    
    async def search(
        self,
        query: str,
        user_id: UUID,
        db: AsyncSession,
        folder_id: UUID | None = None,
        unfiled: bool = False,
        limit: int = 20,
        offset: int = 0,
        min_score: float = 0.3,
        include_archived: bool = False,
    ) -> tuple[list[SearchResult], dict[str, float]]:
        """
        Perform hybrid search combining vector and full-text search in a single query.
        
        Returns:
            Tuple of (results, timing_metrics)
        """
        timing = {}
        start_time = time.time()
        
        # Initialize embedding service
        if self.embedding_service is None:
            self.embedding_service = await get_embedding_service()
        
        # Generate query embedding
        query_embedding = await self.embedding_service.aembed_query(query)
        
        # Perform combined hybrid search
        hybrid_start = time.time()
        results = await self._hybrid_search_combined(
            query=query,
            query_embedding=query_embedding,
            user_id=user_id,
            db=db,
            folder_id=folder_id,
            unfiled=unfiled,
            limit=limit,
            offset=offset,
            min_score=min_score,
            include_archived=include_archived
        )
        timing['hybrid_search_ms'] = (time.time() - hybrid_start) * 1000
        
        timing['total_time_ms'] = (time.time() - start_time) * 1000
        
        return results, timing
    
    def _get_word_variations(self, query: str, min_word_length: int = 3) -> list[str]:
        """
        Generate word variations for fuzzy matching.
        
        For a query like "angluar patterns", returns:
        - Individual words: ["angluar", "patterns"]
        - Only words >= min_word_length are considered
        """
        # Split query into words
        words = query.lower().split()
        
        # Filter words by minimum length
        significant_words = [w for w in words if len(w) >= min_word_length]
        
        return significant_words
    
    def _build_fuzzy_conditions(
        self,
        query: str,
        filename_column,
        text_column,
        similarity_threshold: float = 0.3
    ):
        """
        Build fuzzy search conditions for PostgreSQL.
        
        For each word in the query, check if any word in the document
        has high trigram similarity.
        """
        words = self._get_word_variations(query)
        
        if not words:
            return None
        
        conditions = []
        
        for word in words:
            # For each word, create a condition that checks similarity
            # Using word_similarity for better partial matching
            # Compare with lowercase versions for case-insensitive matching
            conditions.extend([
                func.word_similarity(word.lower(), func.lower(filename_column)) >= similarity_threshold,
                func.word_similarity(word.lower(), func.lower(text_column)) >= similarity_threshold,
            ])
        
        return or_(*conditions) if conditions else None
    
    async def _hybrid_search_combined(
        self,
        query: str,
        query_embedding: list[float],
        user_id: UUID,
        db: AsyncSession,
        folder_id: UUID | None,
        unfiled: bool,
        limit: int,
        offset: int,
        min_score: float,
        include_archived: bool
    ) -> list[SearchResult]:
        """
        Perform hybrid search combining vector and full-text in a single query.
        Uses PostgreSQL tsvector for full-text and pgvector for similarity.
        """
        try:
            # Create tsquery for full-text search
            tsquery = func.plainto_tsquery('english', query)
            
            # Get fuzzy search conditions
            fuzzy_conditions = self._build_fuzzy_conditions(
                query,
                Document.filename,
                DocumentChunk.chunk_text,
                self.settings.trigram_similarity_threshold
            )
            
            
            # Calculate best word similarity for scoring
            words = self._get_word_variations(query)
            if words:
                # For each word, find the best similarity match
                word_similarities = []
                for word in words:
                    word_similarities.extend([
                        func.word_similarity(word.lower(), func.lower(Document.filename)),
                        func.word_similarity(word.lower(), func.lower(DocumentChunk.chunk_text))
                    ])
                trigram_sim_expr = func.greatest(*word_similarities) if word_similarities else cast(0.0, Float)
            else:
                trigram_sim_expr = cast(0.0, Float)
            
            # Build the hybrid search query with trigram similarity
            hybrid_query = (
                select(
                    DocumentChunk,
                    Document,
                    # Full-text rank using ts_rank_cd (cover density)
                    func.ts_rank_cd(
                        DocumentChunk.search_vector,
                        tsquery
                    ).label('text_rank'),
                    # Vector similarity (1 - cosine_distance = similarity)
                    (1 - DocumentChunk.embedding.cosine_distance(query_embedding)).label('vector_similarity'),
                    # Trigram similarity for fuzzy matching
                    trigram_sim_expr.label('trigram_similarity'),
                    # Combined score: weighted sum of all three scores
                    (
                        self.weights.fulltext_weight * func.ts_rank_cd(DocumentChunk.search_vector, tsquery) +
                        self.weights.vector_weight * (1 - DocumentChunk.embedding.cosine_distance(query_embedding)) +
                        self.settings.fuzzy_weight * trigram_sim_expr
                    ).label('combined_score'),
                    # Create snippet with highlighting
                    func.ts_headline(
                        'english',
                        DocumentChunk.chunk_text,
                        tsquery,
                        'StartSel=<mark>, StopSel=</mark>, MinWords=20, MaxWords=50'
                    ).label('snippet')
                )
                .join(Document)
                .where(
                    and_(
                        Document.user_id == user_id,
                        # Require either text match OR high vector similarity OR fuzzy match
                        or_(
                            DocumentChunk.search_vector.op('@@')(tsquery),
                            DocumentChunk.embedding.cosine_distance(query_embedding) < 0.5,  # similarity > 0.5
                            fuzzy_conditions  # Word-level fuzzy matching
                        ) if fuzzy_conditions is not None else or_(
                            DocumentChunk.search_vector.op('@@')(tsquery),
                            DocumentChunk.embedding.cosine_distance(query_embedding) < 0.5
                        )
                    )
                )
                .options(
                    selectinload(Document.tags),
                    selectinload(Document.folder)
                )
            )
            
            # Apply filters
            if not include_archived:
                hybrid_query = hybrid_query.where(Document.archived_at.is_(None))
            
            if folder_id:
                hybrid_query = hybrid_query.where(Document.folder_id == folder_id)
            elif unfiled:
                hybrid_query = hybrid_query.where(Document.folder_id.is_(None))
            
            # Order by combined score and apply limit
            hybrid_query = hybrid_query.order_by(text('combined_score DESC')).limit(limit * 2)
            
            # Execute query
            result = await db.execute(hybrid_query)
            rows = result.all()
            
            
            # Group by document, keeping best scoring chunk
            doc_results = {}
            for row in rows:
                chunk = row.DocumentChunk
                doc = row.Document
                text_rank = float(row.text_rank) if row.text_rank else 0.0
                vector_sim = float(row.vector_similarity) if row.vector_similarity else 0.0
                trigram_sim = float(row.trigram_similarity) if row.trigram_similarity else 0.0
                combined = float(row.combined_score) if row.combined_score else 0.0
                snippet = row.snippet or chunk.chunk_text[:150]
                
                if combined < min_score:
                    continue
                
                if doc.id not in doc_results or combined > doc_results[doc.id].relevance_score:
                    doc_results[doc.id] = SearchResult(
                        document_id=doc.id,
                        filename=doc.filename,
                        title=None,
                        snippet=snippet,
                        relevance_score=combined,
                        vector_score=vector_sim,
                        fulltext_score=text_rank,
                        tags=[tag.name for tag in doc.tags],
                        folder_name=doc.folder.name if doc.folder else None,
                        created_at=doc.created_at,
                        matched_chunks=[{
                            "chunk_index": chunk.chunk_index,
                            "text_rank": text_rank,
                            "vector_similarity": vector_sim,
                            "trigram_similarity": trigram_sim,
                            "snippet": snippet
                        }],
                        explanation=f"Match scores - Text: {text_rank:.3f}, Vector: {vector_sim:.3f}, Fuzzy: {trigram_sim:.3f}"
                    )
                else:
                    # Add to matched chunks if same document
                    doc_results[doc.id].matched_chunks.append({
                        "chunk_index": chunk.chunk_index,
                        "text_rank": text_rank,
                        "vector_similarity": vector_sim,
                        "trigram_similarity": trigram_sim,
                        "snippet": snippet
                    })
            
            # Convert to list and sort by relevance
            results = list(doc_results.values())
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            # Apply pagination
            return results[offset:offset + limit]
            
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            # Fallback to simpler search
            return await self._fallback_search(
                query, user_id, db, folder_id, unfiled, limit, offset, include_archived
            )
    
    async def _fallback_search(
        self,
        query: str,
        user_id: UUID,
        db: AsyncSession,
        folder_id: UUID | None,
        unfiled: bool,
        limit: int,
        offset: int,
        include_archived: bool
    ) -> list[SearchResult]:
        """Fallback to simple text search if hybrid fails."""
        search_pattern = f"%{query}%"
        
        query_obj = (
            select(Document)
            .where(
                and_(
                    Document.user_id == user_id,
                    or_(
                        Document.filename.ilike(search_pattern),
                        Document.extracted_text.ilike(search_pattern)
                    )
                )
            )
            .options(selectinload(Document.tags))
        )
        
        if not include_archived:
            query_obj = query_obj.where(Document.archived_at.is_(None))
        
        if folder_id:
            query_obj = query_obj.where(Document.folder_id == folder_id)
        elif unfiled:
            query_obj = query_obj.where(Document.folder_id.is_(None))
        
        query_obj = query_obj.limit(limit).offset(offset)
        
        result = await db.execute(query_obj)
        documents = result.scalars().all()
        
        results = []
        for doc in documents:
            snippet = ""
            if doc.extracted_text:
                # Find query in text
                lower_text = doc.extracted_text.lower()
                lower_query = query.lower()
                pos = lower_text.find(lower_query)
                if pos != -1:
                    start = max(0, pos - 50)
                    end = min(len(doc.extracted_text), pos + len(query) + 100)
                    snippet = doc.extracted_text[start:end]
                    if start > 0:
                        snippet = "..." + snippet
                    if end < len(doc.extracted_text):
                        snippet = snippet + "..."
                else:
                    snippet = doc.extracted_text[:150] + "..."
            else:
                snippet = doc.filename
            
            results.append(SearchResult(
                document_id=doc.id,
                filename=doc.filename,
                title=None,
                snippet=snippet,
                relevance_score=0.5,  # Default score for fallback
                tags=[tag.name for tag in doc.tags],
                created_at=doc.created_at
            ))
        
        return results