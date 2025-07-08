"""Add tsvector columns for full-text search.

Revision ID: 003_add_tsvector_columns
Revises: 002_performance_indexes
Create Date: 2025-01-08 17:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003_add_tsvector_columns'
down_revision: Union[str, None] = '002_performance_indexes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add tsvector columns and indexes for full-text search."""
    
    # Add search_vector column to documents table
    op.add_column('documents', 
        sa.Column('search_vector', postgresql.TSVECTOR(), nullable=True)
    )
    
    # Add search_vector column to document_chunks table
    op.add_column('document_chunks',
        sa.Column('search_vector', postgresql.TSVECTOR(), nullable=True)
    )
    
    # Create function to update document search vector
    op.execute("""
        CREATE OR REPLACE FUNCTION update_document_search_vector() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector := 
                setweight(to_tsvector('english', COALESCE(NEW.filename, '')), 'A') ||
                setweight(to_tsvector('english', COALESCE(NEW.extracted_text, '')), 'B');
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create function to update chunk search vector
    op.execute("""
        CREATE OR REPLACE FUNCTION update_chunk_search_vector() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector := to_tsvector('english', COALESCE(NEW.chunk_text, ''));
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create triggers for automatic search vector updates
    op.execute("""
        CREATE TRIGGER update_document_search_vector_trigger
        BEFORE INSERT OR UPDATE OF filename, extracted_text
        ON documents
        FOR EACH ROW
        EXECUTE FUNCTION update_document_search_vector();
    """)
    
    op.execute("""
        CREATE TRIGGER update_chunk_search_vector_trigger
        BEFORE INSERT OR UPDATE OF chunk_text
        ON document_chunks
        FOR EACH ROW
        EXECUTE FUNCTION update_chunk_search_vector();
    """)
    
    # Update existing documents
    op.execute("""
        UPDATE documents 
        SET search_vector = 
            setweight(to_tsvector('english', COALESCE(filename, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(extracted_text, '')), 'B')
        WHERE search_vector IS NULL;
    """)
    
    # Update existing chunks
    op.execute("""
        UPDATE document_chunks 
        SET search_vector = to_tsvector('english', COALESCE(chunk_text, ''))
        WHERE search_vector IS NULL;
    """)
    
    # Create GIN indexes for full-text search
    op.create_index(
        'idx_documents_search_vector',
        'documents',
        ['search_vector'],
        postgresql_using='gin'
    )
    
    op.create_index(
        'idx_document_chunks_search_vector',
        'document_chunks',
        ['search_vector'],
        postgresql_using='gin'
    )
    
    # Create specialized index for vector + text hybrid search
    op.execute("""
        CREATE INDEX idx_chunks_hybrid_search 
        ON document_chunks 
        USING gin(search_vector) 
        WHERE embedding IS NOT NULL;
    """)


def downgrade() -> None:
    """Remove tsvector columns and related objects."""
    
    # Drop indexes
    op.drop_index('idx_chunks_hybrid_search', 'document_chunks')
    op.drop_index('idx_document_chunks_search_vector', 'document_chunks')
    op.drop_index('idx_documents_search_vector', 'documents')
    
    # Drop triggers
    op.execute('DROP TRIGGER IF EXISTS update_chunk_search_vector_trigger ON document_chunks')
    op.execute('DROP TRIGGER IF EXISTS update_document_search_vector_trigger ON documents')
    
    # Drop functions
    op.execute('DROP FUNCTION IF EXISTS update_chunk_search_vector()')
    op.execute('DROP FUNCTION IF EXISTS update_document_search_vector()')
    
    # Drop columns
    op.drop_column('document_chunks', 'search_vector')
    op.drop_column('documents', 'search_vector')