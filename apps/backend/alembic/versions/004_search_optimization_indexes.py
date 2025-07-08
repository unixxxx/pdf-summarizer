"""Add search optimization indexes.

Revision ID: 004_search_optimization_indexes
Revises: 003_add_tsvector_columns
Create Date: 2025-01-08 18:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '004_search_optimization_indexes'
down_revision: Union[str, None] = '003_add_tsvector_columns'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add indexes for search optimization."""
    
    # 1. Vector search optimization - HNSW index for document chunks
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding_hnsw 
        ON document_chunks USING hnsw (embedding vector_cosine_ops) 
        WITH (m = 16, ef_construction = 64)
        WHERE embedding IS NOT NULL
    """)
    
    # 2. Composite index for hybrid search filtering
    op.create_index(
        'idx_document_chunks_document_id_chunk_index',
        'document_chunks',
        ['document_id', 'chunk_index']
    )
    
    # 3. Index for tag search - tags are global, not user-specific
    # Name index already exists from initial schema (ix_tags_name)
    
    # 4. Index for summary search - summaries are in a separate table
    # Could add: CREATE INDEX ON summaries USING gin(to_tsvector('english', summary_text))
    
    # 5. Composite index for document filtering in search
    op.create_index(
        'idx_documents_user_folder_archived',
        'documents',
        ['user_id', 'folder_id', 'archived_at'],
        postgresql_where=sa.text('processed_at IS NOT NULL')
    )
    
    # 6. Index for unfiled documents search
    op.create_index(
        'idx_documents_user_unfiled',
        'documents',
        ['user_id', 'created_at'],
        postgresql_where=sa.text('folder_id IS NULL AND archived_at IS NULL')
    )
    
    # 7. Covering index for document metadata retrieval
    op.create_index(
        'idx_documents_search_covering',
        'documents',
        ['user_id', 'status', 'created_at'],
        postgresql_include=['filename', 'file_size', 'page_count']
    )
    
    # 8. Index for recent documents (commonly searched)
    # Note: Can't use CURRENT_DATE in partial index as it's not immutable
    # Instead, create a general index for user_id and created_at
    op.create_index(
        'idx_documents_user_created_desc',
        'documents',
        ['user_id', sa.text('created_at DESC')],
        postgresql_where=sa.text("archived_at IS NULL")
    )


def downgrade() -> None:
    """Drop search optimization indexes."""
    
    op.drop_index('idx_documents_user_created_desc', 'documents')
    op.drop_index('idx_documents_search_covering', 'documents')
    op.drop_index('idx_documents_user_unfiled', 'documents')
    op.drop_index('idx_documents_user_folder_archived', 'documents')
    op.drop_index('idx_document_chunks_document_id_chunk_index', 'document_chunks')
    op.execute('DROP INDEX IF EXISTS idx_document_chunks_embedding_hnsw')