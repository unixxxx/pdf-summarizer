"""Add comprehensive performance indexes.

Revision ID: 002_performance_indexes
Revises: 001_initial_schema
Create Date: 2025-01-08 16:30:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '002_performance_indexes'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance indexes for common query patterns."""
    
    # Enable pg_trgm extension for text search
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')
    
    # 1. User Authentication Indexes
    op.create_index('idx_users_provider_provider_id', 'users', ['provider', 'provider_id'])
    op.create_index('idx_users_email_lower', 'users', [sa.text('lower(email)')])
    
    # 2. Document Query Indexes
    op.create_index('idx_documents_status', 'documents', ['status'], 
                    postgresql_where=sa.text('archived_at IS NULL'))
    op.create_index('idx_documents_user_id_status', 'documents', ['user_id', 'status'],
                    postgresql_where=sa.text('archived_at IS NULL'))
    op.create_index('idx_documents_filename_trgm', 'documents', ['filename'],
                    postgresql_using='gin', postgresql_ops={'filename': 'gin_trgm_ops'})
    op.create_index('idx_documents_folder_id_created_at', 'documents', 
                    ['folder_id', sa.text('created_at DESC')],
                    postgresql_where=sa.text('archived_at IS NULL'))
    op.create_index('idx_documents_file_hash_user_id', 'documents', ['file_hash', 'user_id'],
                    postgresql_where=sa.text('archived_at IS NULL'))
    
    # 3. Timestamp-based Indexes
    op.create_index('idx_documents_updated_at', 'documents', [sa.text('updated_at DESC')])
    op.create_index('idx_documents_processed_at', 'documents', ['processed_at'],
                    postgresql_where=sa.text('processed_at IS NOT NULL'))
    op.create_index('idx_folders_updated_at', 'folders', [sa.text('updated_at DESC')])
    op.create_index('idx_chats_updated_at', 'chats', [sa.text('updated_at DESC')])
    
    # 4. Archive Indexes
    op.create_index('idx_documents_user_id_archived_at', 'documents', 
                    ['user_id', sa.text('archived_at DESC')],
                    postgresql_where=sa.text('archived_at IS NOT NULL'))
    op.create_index('idx_folders_user_id_archived_at', 'folders',
                    ['user_id', sa.text('archived_at DESC')],
                    postgresql_where=sa.text('archived_at IS NOT NULL'))
    
    # 5. Association Table Indexes
    op.create_index('idx_document_tags_tag_id', 'document_tags', ['tag_id'])
    op.create_index('idx_document_tags_created_at', 'document_tags', [sa.text('created_at DESC')])
    op.create_index('idx_folder_tags_tag_id', 'folder_tags', ['tag_id'])
    op.create_index('idx_folder_tags_created_at', 'folder_tags', [sa.text('created_at DESC')])
    
    # 6. Folder Hierarchy Indexes
    op.create_index('idx_folders_parent_id', 'folders', ['parent_id'],
                    postgresql_where=sa.text('archived_at IS NULL'))
    op.create_index('idx_folders_user_id_parent_id', 'folders', ['user_id', 'parent_id'],
                    postgresql_where=sa.text('archived_at IS NULL'))
    op.create_index('idx_folders_user_id_name', 'folders', ['user_id', 'name'],
                    postgresql_where=sa.text('archived_at IS NULL'))
    
    # 7. Job Progress Indexes
    op.create_index('idx_job_progress_stage', 'job_progress', ['stage'])
    op.create_index('idx_job_progress_completed_at', 'job_progress', [sa.text('completed_at DESC')],
                    postgresql_where=sa.text('completed_at IS NOT NULL'))
    op.create_index('idx_job_progress_user_id_started_at', 'job_progress',
                    ['user_id', sa.text('started_at DESC')],
                    postgresql_where=sa.text('completed_at IS NULL'))
    
    # 8. Summary Indexes
    op.create_index('idx_summaries_document_id', 'summaries', ['document_id'])
    op.create_index('idx_summaries_user_id_created_at', 'summaries', 
                    ['user_id', sa.text('created_at DESC')])
    
    # 9. Chat Indexes
    op.create_index('idx_chats_user_id_updated_at', 'chats', ['user_id', sa.text('updated_at DESC')])
    op.create_index('idx_chat_messages_chat_id_created_at', 'chat_messages',
                    ['chat_id', sa.text('created_at')])
    
    # 10. Advanced Vector Index for Tags (HNSW is more efficient than IVFFlat for smaller datasets)
    op.execute("""
        CREATE INDEX idx_tags_embedding_hnsw 
        ON tags USING hnsw (embedding vector_cosine_ops) 
        WITH (m = 16, ef_construction = 64)
        WHERE embedding IS NOT NULL
    """)


def downgrade() -> None:
    """Drop all performance indexes."""
    # Drop indexes in reverse order
    op.execute('DROP INDEX IF EXISTS idx_tags_embedding_hnsw')
    
    op.drop_index('idx_chat_messages_chat_id_created_at', 'chat_messages')
    op.drop_index('idx_chats_user_id_updated_at', 'chats')
    
    op.drop_index('idx_summaries_user_id_created_at', 'summaries')
    op.drop_index('idx_summaries_document_id', 'summaries')
    
    op.drop_index('idx_job_progress_user_id_started_at', 'job_progress')
    op.drop_index('idx_job_progress_completed_at', 'job_progress')
    op.drop_index('idx_job_progress_stage', 'job_progress')
    
    op.drop_index('idx_folders_user_id_name', 'folders')
    op.drop_index('idx_folders_user_id_parent_id', 'folders')
    op.drop_index('idx_folders_parent_id', 'folders')
    
    op.drop_index('idx_folder_tags_created_at', 'folder_tags')
    op.drop_index('idx_folder_tags_tag_id', 'folder_tags')
    op.drop_index('idx_document_tags_created_at', 'document_tags')
    op.drop_index('idx_document_tags_tag_id', 'document_tags')
    
    op.drop_index('idx_folders_user_id_archived_at', 'folders')
    op.drop_index('idx_documents_user_id_archived_at', 'documents')
    
    op.drop_index('idx_chats_updated_at', 'chats')
    op.drop_index('idx_folders_updated_at', 'folders')
    op.drop_index('idx_documents_processed_at', 'documents')
    op.drop_index('idx_documents_updated_at', 'documents')
    
    op.drop_index('idx_documents_file_hash_user_id', 'documents')
    op.drop_index('idx_documents_folder_id_created_at', 'documents')
    op.drop_index('idx_documents_filename_trgm', 'documents')
    op.drop_index('idx_documents_user_id_status', 'documents')
    op.drop_index('idx_documents_status', 'documents')
    
    op.drop_index('idx_users_email_lower', 'users')
    op.drop_index('idx_users_provider_provider_id', 'users')