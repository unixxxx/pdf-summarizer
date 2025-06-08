"""Embeddings service for generating and managing document embeddings."""

import json
from typing import List, Optional, Tuple
from uuid import UUID

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..common.exceptions import OpenAIConfigError
from ..config import Settings
from ..database.models import Document, DocumentChunk


class EmbeddingsService:
    """Service for generating and managing document embeddings."""

    def __init__(self, settings: Settings):
        self.settings = settings
        
        # Initialize embeddings model based on provider
        if settings.llm_provider.lower() == "ollama":
            self.embeddings = OllamaEmbeddings(
                base_url=settings.ollama_base_url,
                model=settings.ollama_model,
            )
            self.embedding_dimension = 4096  # Default for most Ollama models
        else:
            # Use OpenAI
            if not settings.openai_api_key:
                raise OpenAIConfigError()
            
            self.embeddings = OpenAIEmbeddings(
                api_key=settings.openai_api_key,
                model="text-embedding-3-small",
            )
            self.embedding_dimension = 1536  # OpenAI embedding dimension
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
    
    async def create_document_embeddings(
        self,
        document_id: str,
        text: str,
        db: AsyncSession,
    ) -> List[DocumentChunk]:
        """Create embeddings for a document and store them in the database."""
        # Split text into chunks
        chunks = self.text_splitter.split_text(text)
        
        # Generate embeddings for all chunks
        embeddings = await self.embeddings.aembed_documents(chunks)
        
        # Create DocumentChunk records
        document_chunks = []
        for idx, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
            # Create metadata
            metadata = {
                "chunk_index": idx,
                "total_chunks": len(chunks),
                "chunk_size": len(chunk_text),
            }
            
            chunk = DocumentChunk(
                document_id=document_id,
                chunk_index=idx,
                chunk_text=chunk_text,
                embedding=embedding,
                chunk_metadata=json.dumps(metadata),
            )
            document_chunks.append(chunk)
            db.add(chunk)
        
        # Don't commit here - let the caller handle transaction boundaries
        await db.flush()
        return document_chunks
    
    async def search_similar_chunks(
        self,
        query: str,
        document_id: Optional[str],
        db: AsyncSession,
        limit: int = 5,
    ) -> List[Tuple[DocumentChunk, float]]:
        """Search for similar chunks using pgvector's SQL similarity operators."""
        # Generate embedding for the query
        query_embedding = await self.embeddings.aembed_query(query)
        
        # Convert document_id to UUID if needed
        if document_id and isinstance(document_id, str):
            from uuid import UUID
            document_id = UUID(document_id)
        
        # Convert embedding to a format pgvector understands
        # pgvector expects a string representation like '[1,2,3]'
        import json
        query_embedding_str = json.dumps(query_embedding)
        
        # Use raw SQL for vector operations as SQLAlchemy's support is limited
        from sqlalchemy import text
        
        # Build the query using raw SQL with pgvector
        if document_id:
            # Query with document filter
            sql = text("""
                SELECT 
                    dc.*,
                    1 - (dc.embedding <=> CAST(:query_embedding AS vector)) as similarity
                FROM document_chunks dc
                WHERE 
                    dc.embedding IS NOT NULL
                    AND dc.document_id = CAST(:document_id AS uuid)
                    AND dc.embedding <=> CAST(:query_embedding AS vector) <= :max_distance
                ORDER BY dc.embedding <=> CAST(:query_embedding AS vector)
                LIMIT :limit
            """)
        else:
            # Query without document filter
            sql = text("""
                SELECT 
                    dc.*,
                    1 - (dc.embedding <=> CAST(:query_embedding AS vector)) as similarity
                FROM document_chunks dc
                WHERE 
                    dc.embedding IS NOT NULL
                    AND dc.embedding <=> CAST(:query_embedding AS vector) <= :max_distance
                ORDER BY dc.embedding <=> CAST(:query_embedding AS vector)
                LIMIT :limit
            """)
        
        # Calculate max distance from min similarity
        min_similarity = 0.5
        max_distance = 1 - min_similarity  # For normalized cosine distance
        
        # Execute query
        params = {
            "query_embedding": query_embedding_str,
            "max_distance": max_distance,
            "limit": limit
        }
        
        if document_id:
            params["document_id"] = str(document_id)
            
        result = await db.execute(sql, params)
        rows = result.mappings().all()
        
        # Transform results back to DocumentChunk objects
        chunks_with_similarity = []
        for row in rows:
            # Create DocumentChunk from row data
            chunk = DocumentChunk(
                id=row['id'],
                document_id=row['document_id'],
                chunk_index=row['chunk_index'],
                chunk_text=row['chunk_text'],
                embedding=row['embedding'],
                chunk_metadata=row['chunk_metadata'],
                created_at=row['created_at']
            )
            similarity = float(row['similarity'])
            chunks_with_similarity.append((chunk, similarity))
        
        # If we got too few results due to similarity threshold, 
        # fall back to getting at least 3 without threshold
        if len(chunks_with_similarity) < 3 and document_id:
            fallback_sql = text("""
                SELECT 
                    dc.*,
                    1 - (dc.embedding <=> CAST(:query_embedding AS vector)) as similarity
                FROM document_chunks dc
                WHERE 
                    dc.embedding IS NOT NULL
                    AND dc.document_id = CAST(:document_id AS uuid)
                ORDER BY dc.embedding <=> CAST(:query_embedding AS vector)
                LIMIT 3
            """)
            
            result = await db.execute(
                fallback_sql,
                {
                    "query_embedding": query_embedding_str,
                    "document_id": str(document_id)
                }
            )
            rows = result.mappings().all()
            
            chunks_with_similarity = []
            for row in rows:
                chunk = DocumentChunk(
                    id=row['id'],
                    document_id=row['document_id'],
                    chunk_index=row['chunk_index'],
                    chunk_text=row['chunk_text'],
                    embedding=row['embedding'],
                    chunk_metadata=row['chunk_metadata'],
                    created_at=row['created_at']
                )
                similarity = float(row['similarity'])
                chunks_with_similarity.append((chunk, similarity))
        
        return chunks_with_similarity
    
    async def get_document_chunks(
        self,
        document_id: str,
        db: AsyncSession,
    ) -> List[DocumentChunk]:
        """Get all chunks for a document."""
        result = await db.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
        )
        return result.scalars().all()
    
    async def delete_document_embeddings(
        self,
        document_id: str,
        db: AsyncSession,
    ) -> None:
        """Delete all embeddings for a document."""
        result = await db.execute(
            select(DocumentChunk).where(DocumentChunk.document_id == document_id)
        )
        chunks = result.scalars().all()
        
        for chunk in chunks:
            await db.delete(chunk)
        
        # Don't commit here - let the caller handle transaction boundaries
        await db.flush()