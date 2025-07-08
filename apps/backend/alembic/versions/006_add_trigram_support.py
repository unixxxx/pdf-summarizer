"""Add trigram support for fuzzy text search.

Revision ID: 006_add_trigram_support
Revises: 004_search_optimization_indexes
Create Date: 2025-01-09 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '006_add_trigram_support'
down_revision: Union[str, None] = '004_search_optimization_indexes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add trigram extension and indexes for fuzzy search."""
    
    # Enable pg_trgm extension
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    
    # Create trigram indexes for fuzzy filename search (check if exists)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_documents_filename_trgm 
        ON documents 
        USING gin (filename gin_trgm_ops)
    """)
    
    # Create trigram indexes for fuzzy text search
    # Note: This can be expensive on large text fields, so we'll create it conditionally
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_documents_extracted_text_trgm 
        ON documents 
        USING gin (extracted_text gin_trgm_ops)
        WHERE extracted_text IS NOT NULL
    """)
    
    # Create trigram index for document chunks
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_document_chunks_chunk_text_trgm 
        ON document_chunks 
        USING gin (chunk_text gin_trgm_ops)
    """)
    
    # Create trigram indexes for tags
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_tags_name_trgm 
        ON tags 
        USING gin (name gin_trgm_ops)
    """)
    
    # Create similarity threshold setting (default 0.3)
    op.execute("SET pg_trgm.similarity_threshold = 0.3")
    
    # Create function to search with trigram similarity
    op.execute("""
        CREATE OR REPLACE FUNCTION search_documents_fuzzy(
            search_term TEXT,
            user_id_param UUID,
            similarity_threshold FLOAT DEFAULT 0.3
        )
        RETURNS TABLE (
            document_id UUID,
            filename TEXT,
            similarity_score FLOAT,
            match_type TEXT
        ) AS $$
        BEGIN
            RETURN QUERY
            SELECT 
                d.id,
                d.filename,
                similarity(d.filename, search_term) as similarity_score,
                'filename' as match_type
            FROM documents d
            WHERE d.user_id = user_id_param
                AND d.archived_at IS NULL
                AND similarity(d.filename, search_term) > similarity_threshold
            
            UNION
            
            SELECT 
                d.id,
                d.filename,
                similarity(d.extracted_text, search_term) as similarity_score,
                'content' as match_type
            FROM documents d
            WHERE d.user_id = user_id_param
                AND d.archived_at IS NULL
                AND d.extracted_text IS NOT NULL
                AND similarity(d.extracted_text, search_term) > similarity_threshold
            
            ORDER BY similarity_score DESC;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Add comment explaining the indexes
    op.execute("""
        COMMENT ON INDEX idx_documents_filename_trgm IS 
        'Trigram index for fuzzy filename search with typo tolerance';
    """)
    
    op.execute("""
        COMMENT ON INDEX idx_documents_extracted_text_trgm IS 
        'Trigram index for fuzzy content search - may be slow to build on large datasets';
    """)


def downgrade() -> None:
    """Remove trigram support."""
    
    # Drop function
    op.execute("DROP FUNCTION IF EXISTS search_documents_fuzzy")
    
    # Drop indexes
    op.drop_index('idx_tags_name_trgm', 'tags')
    op.execute("DROP INDEX IF EXISTS idx_document_chunks_chunk_text_trgm")
    op.execute("DROP INDEX IF EXISTS idx_documents_extracted_text_trgm")
    op.drop_index('idx_documents_filename_trgm', 'documents')
    
    # Note: We don't drop the extension as other parts of the database might use it
    # op.execute("DROP EXTENSION IF EXISTS pg_trgm")