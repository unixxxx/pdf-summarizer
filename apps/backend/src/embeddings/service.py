"""Embeddings service for generating and managing embeddings for documents and tags."""

import json
import logging
from uuid import UUID

from langchain.text_splitter import RecursiveCharacterTextSplitter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..common.exceptions import EmbeddingError
from ..common.llm_factory import UnifiedLLMFactory
from ..common.retry import retry_on_llm_error
from ..config import Settings
from ..database.models import DocumentChunk, Tag

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """Service for generating and managing embeddings for documents and tags."""

    def __init__(self, settings: Settings, factory: UnifiedLLMFactory):
        self.settings = settings
        
        # Use unified factory for embeddings model
        self.embeddings, self.embedding_dimension = factory.create_embeddings_model()
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        
        # Track if indexes have been created
        self._indexes_created = False
    
    async def create_document_embeddings(
        self,
        document_id: str,
        text: str,
        db: AsyncSession,
    ) -> list[DocumentChunk]:
        """Create embeddings for a document and store them in the database."""
        # Split text into chunks
        chunks = self.text_splitter.split_text(text)
        
        # Process embeddings in batches to reduce memory usage
        batch_size = 10
        all_embeddings = []
        
        @retry_on_llm_error(max_attempts=3)
        async def _generate_batch_embeddings(batch: list[str]) -> list:
            try:
                return await self.embeddings.aembed_documents(batch)
            except Exception as e:
                logger.error(f"Failed to generate embeddings for batch: {str(e)}")
                raise EmbeddingError(f"Failed to generate embeddings: {str(e)}")
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            try:
                batch_embeddings = await _generate_batch_embeddings(batch)
                all_embeddings.extend(batch_embeddings)
            except EmbeddingError as e:
                logger.error(f"Skipping batch {i//batch_size} due to error: {e}")
                # Add None placeholders for failed embeddings
                all_embeddings.extend([None] * len(batch))
        
        # Create DocumentChunk records
        document_chunks = []
        for idx, (chunk_text, embedding) in enumerate(zip(chunks, all_embeddings)):
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
        
        # Ensure HNSW indexes are created after first embeddings
        await self.ensure_hnsw_indexes(db)
        
        return document_chunks
    
    async def search_similar_chunks(
        self,
        query: str,
        document_id: str | None,
        db: AsyncSession,
        limit: int = 5,
        similarity_threshold: float = 0.5,
    ) -> list[tuple[DocumentChunk, float]]:
        """Search for similar chunks using pgvector's SQL similarity operators."""
        # Generate embedding for the query with retry
        @retry_on_llm_error(max_attempts=3)
        async def _generate_query_embedding():
            try:
                return await self.embeddings.aembed_query(query)
            except Exception as e:
                logger.error(f"Failed to generate query embedding: {str(e)}")
                raise EmbeddingError(f"Failed to generate query embedding: {str(e)}")
        
        try:
            query_embedding = await _generate_query_embedding()
        except EmbeddingError:
            logger.error("Failed to generate query embedding after retries")
            return []
        
        # Convert document_id to UUID if needed
        if document_id and isinstance(document_id, str):
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
        
        # Set HNSW search parameters for optimal performance
        # ef_search controls the search accuracy/speed tradeoff
        # Higher values = more accurate but slower
        await db.execute(text("SET LOCAL hnsw.ef_search = 100;"))
        
        # Calculate max distance from min similarity
        max_distance = 1 - similarity_threshold  # For normalized cosine distance
        
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
    
    # Tag embedding methods
    async def _generate_tag_embedding(self, tag_name: str) -> list[float]:
        """Generate embedding for a tag name."""
        # Generate embedding for the tag name
        embedding = await self.embeddings.aembed_query(tag_name)
        return embedding
    
    async def update_tag_embedding(
        self,
        tag_id: UUID,
        tag_name: str,
        db: AsyncSession,
    ) -> None:
        """Update or create embedding for a tag."""
        # Generate embedding
        embedding = await self._generate_tag_embedding(tag_name)
        
        # Convert embedding to a format pgvector understands
        embedding_str = json.dumps(embedding)
        
        # Update tag with embedding using raw SQL
        sql = text("""
            UPDATE tags 
            SET embedding = CAST(:embedding AS vector)
            WHERE id = :tag_id
        """)
        
        await db.execute(sql, {
            "embedding": embedding_str,
            "tag_id": str(tag_id)
        })
        
        await db.flush()
        
        # Ensure HNSW indexes are created after first embeddings
        await self.ensure_hnsw_indexes(db)
    
    async def find_similar_tags(
        self,
        tag_name: str,
        db: AsyncSession,
        similarity_threshold: float = 0.85,
        limit: int = 5,
    ) -> list[tuple[Tag, float]]:
        """Find existing tags similar to the given tag name."""
        # Generate embedding for the query tag
        query_embedding = await self._generate_tag_embedding(tag_name)
        query_embedding_str = json.dumps(query_embedding)
        
        # Set HNSW search parameters for optimal performance
        await db.execute(text("SET LOCAL hnsw.ef_search = 100;"))
        
        # Convert similarity threshold to distance
        # For cosine distance: distance = 1 - similarity
        max_distance = 1 - similarity_threshold
        
        # Query for similar tags using pgvector
        sql = text("""
            SELECT 
                t.*,
                1 - (t.embedding <=> CAST(:query_embedding AS vector)) as similarity
            FROM tags t
            WHERE 
                t.embedding IS NOT NULL
                AND t.embedding <=> CAST(:query_embedding AS vector) <= :max_distance
            ORDER BY t.embedding <=> CAST(:query_embedding AS vector)
            LIMIT :limit
        """)
        
        result = await db.execute(sql, {
            "query_embedding": query_embedding_str,
            "max_distance": max_distance,
            "limit": limit
        })
        
        rows = result.mappings().all()
        
        # Transform results back to Tag objects with similarity scores
        tags_with_similarity = []
        for row in rows:
            # Create Tag from row data
            tag = Tag(
                id=row['id'],
                name=row['name'],
                slug=row['slug'],
                description=row['description'],
                color=row['color'],
                embedding=row['embedding'],
                created_at=row['created_at']
            )
            similarity = float(row['similarity'])
            tags_with_similarity.append((tag, similarity))
        
        return tags_with_similarity
    
    async def find_or_create_similar_tag(
        self,
        tag_name: str,
        db: AsyncSession,
        similarity_threshold: float = 0.9,
    ) -> Tag | None:
        """Find a similar existing tag or return None if no similar tag exists."""
        # Find similar tags
        similar_tags = await self.find_similar_tags(
            tag_name=tag_name,
            db=db,
            similarity_threshold=similarity_threshold,
            limit=1
        )
        
        if similar_tags:
            tag, similarity = similar_tags[0]
            logger.info(f"Found similar tag '{tag.name}' for '{tag_name}' with similarity {similarity:.2f}")
            return tag
        
        return None
    
    async def ensure_hnsw_indexes(self, db: AsyncSession) -> None:
        """Create HNSW indexes if they don't exist and we have embeddings."""
        if self._indexes_created or self.embedding_dimension is None:
            return
        
        try:
            # Check if indexes already exist
            result = await db.execute(text("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE indexname IN ('idx_document_chunks_embedding_hnsw', 'idx_tags_embedding_hnsw')
            """))
            existing_indexes = {row[0] for row in result}
            
            # Create document chunks index if needed
            if 'idx_document_chunks_embedding_hnsw' not in existing_indexes:
                # First check if we have any embeddings
                result = await db.execute(text("""
                    SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL
                """))
                count = result.scalar()
                
                if count > 0:
                    logger.info(f"Creating HNSW index for document_chunks with dimension {self.embedding_dimension}")
                    await db.execute(text(f"""
                        CREATE INDEX idx_document_chunks_embedding_hnsw 
                        ON document_chunks 
                        USING hnsw (embedding::vector({self.embedding_dimension}) vector_cosine_ops)
                        WITH (m = 16, ef_construction = 64)
                        WHERE embedding IS NOT NULL
                    """))
                    await db.commit()
                    logger.info("Document chunks HNSW index created successfully")
            
            # Create tags index if needed
            if 'idx_tags_embedding_hnsw' not in existing_indexes:
                # First check if we have any embeddings
                result = await db.execute(text("""
                    SELECT COUNT(*) FROM tags WHERE embedding IS NOT NULL
                """))
                count = result.scalar()
                
                if count > 0:
                    logger.info(f"Creating HNSW index for tags with dimension {self.embedding_dimension}")
                    await db.execute(text(f"""
                        CREATE INDEX idx_tags_embedding_hnsw 
                        ON tags 
                        USING hnsw (embedding::vector({self.embedding_dimension}) vector_cosine_ops)
                        WITH (m = 16, ef_construction = 64)
                        WHERE embedding IS NOT NULL
                    """))
                    await db.commit()
                    logger.info("Tags HNSW index created successfully")
            
            self._indexes_created = True
            
        except Exception as e:
            logger.warning(f"Failed to create HNSW indexes: {str(e)}")
            # Don't fail the operation, just log the warning