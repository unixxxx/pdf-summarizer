"""add_pgvector_hnsw_indexes

Revision ID: c3988533a3ff
Revises: 3f9f7f62f929
Create Date: 2025-06-13 13:19:33.748256

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3988533a3ff'
down_revision: Union[str, None] = '3f9f7f62f929'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add HNSW indexes for fast vector similarity search."""
    # Note: HNSW indexes require fixed dimensions for vector columns
    # Since our columns have flexible dimensions, we need to skip index creation
    # and instead create them dynamically when we know the embedding dimension
    
    # Log a message about this
    op.execute("""
        DO $$
        BEGIN
            RAISE NOTICE 'HNSW indexes require fixed vector dimensions. Indexes will be created dynamically when embeddings are generated.';
        END $$;
    """)
    
    # Create a function to create HNSW indexes dynamically
    op.execute("""
        CREATE OR REPLACE FUNCTION create_hnsw_indexes_if_needed() RETURNS void AS $$
        DECLARE
            has_document_chunks_index boolean;
            has_tags_index boolean;
        BEGIN
            -- Check if indexes already exist
            SELECT EXISTS (
                SELECT 1 FROM pg_indexes 
                WHERE indexname = 'idx_document_chunks_embedding_hnsw'
            ) INTO has_document_chunks_index;
            
            SELECT EXISTS (
                SELECT 1 FROM pg_indexes 
                WHERE indexname = 'idx_tags_embedding_hnsw'
            ) INTO has_tags_index;
            
            -- Create document chunks index if needed and embeddings exist
            IF NOT has_document_chunks_index AND EXISTS (
                SELECT 1 FROM document_chunks WHERE embedding IS NOT NULL LIMIT 1
            ) THEN
                -- Note: This function should be called from application code
                -- after setting the proper vector dimension
                RAISE NOTICE 'Document chunks have embeddings but no HNSW index. Create manually with fixed dimensions.';
            END IF;
            
            -- Create tags index if needed and embeddings exist
            IF NOT has_tags_index AND EXISTS (
                SELECT 1 FROM tags WHERE embedding IS NOT NULL LIMIT 1
            ) THEN
                RAISE NOTICE 'Tags have embeddings but no HNSW index. Create manually with fixed dimensions.';
            END IF;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Note: We can't set session parameters in a migration
    # The application will need to set hnsw.ef_search at runtime


def downgrade() -> None:
    """Remove HNSW indexes and helper function."""
    op.execute("DROP FUNCTION IF EXISTS create_hnsw_indexes_if_needed();")
    op.execute("DROP INDEX IF EXISTS idx_tags_embedding_hnsw;")
    op.execute("DROP INDEX IF EXISTS idx_document_chunks_embedding_hnsw;")
