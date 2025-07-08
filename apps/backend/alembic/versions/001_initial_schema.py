"""Initial consolidated schema for DocuLearn.

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-01-08 16:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables with proper constraints and indexes."""
    
    # Create pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create custom enum types
    op.execute("CREATE TYPE documentstatus AS ENUM ('pending', 'uploading', 'processing', 'completed', 'failed')")
    
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('picture', sa.String(length=500), nullable=True),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('provider_id', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('provider', 'provider_id', name='_provider_user_uc')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # Create folders table (before documents since documents reference folders)
    op.create_table('folders',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(length=7), nullable=True),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('archived_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['parent_id'], ['folders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'name', 'parent_id', name='_user_folder_name_uc')
    )
    op.create_index(op.f('ix_folders_archived_at'), 'folders', ['archived_at'], unique=False)
    op.create_index('idx_folders_deleted_at_null', 'folders', ['id'], unique=False, 
                    postgresql_where=sa.text('archived_at IS NULL'))
    
    # Create documents table
    op.create_table('documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('file_hash', sa.String(length=64), nullable=False),
        sa.Column('page_count', sa.Integer(), nullable=True),
        sa.Column('storage_path', sa.String(length=500), nullable=True),
        sa.Column('extracted_text', sa.Text(), nullable=True),
        sa.Column('word_count', sa.Integer(), nullable=True),
        sa.Column('folder_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', postgresql.ENUM('pending', 'uploading', 'processing', 'completed', 'failed', 
                                           name='documentstatus', create_type=False), 
                  nullable=False, server_default='pending'),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('archived_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['folder_id'], ['folders.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_documents_archived_at'), 'documents', ['archived_at'], unique=False)
    op.create_index(op.f('ix_documents_created_at'), 'documents', ['created_at'], unique=False)
    op.create_index(op.f('ix_documents_file_hash'), 'documents', ['file_hash'], unique=False)
    op.create_index(op.f('ix_documents_folder_id'), 'documents', ['folder_id'], unique=False)
    op.create_index('idx_documents_user_id', 'documents', ['user_id'], unique=False)
    op.create_index('idx_documents_folder_id_user_id', 'documents', ['folder_id', 'user_id'], unique=False)
    op.create_index('idx_documents_deleted_at_null', 'documents', ['id'], unique=False,
                    postgresql_where=sa.text('archived_at IS NULL'))
    
    # Create chats table
    op.create_table('chats',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_chats_user_id_document_id', 'chats', ['user_id', 'document_id'], unique=False)
    
    # Create document_chunks table
    op.create_table('document_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('chunk_text', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(1536), nullable=True),  # Default to OpenAI dimensions, but flexible in practice
        sa.Column('chunk_metadata', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_document_chunks_document_id', 'document_chunks', ['document_id'], unique=False)
    
    # Create ivfflat index for vector similarity search
    op.execute('CREATE INDEX idx_document_chunks_embedding_vector ON document_chunks USING ivfflat (embedding vector_cosine_ops)')
    
    # Create job_progress table
    op.create_table('job_progress',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', sa.String(length=255), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('stage', sa.String(length=50), nullable=False),
        sa.Column('progress', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('last_update', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_id')
    )
    op.create_index(op.f('ix_job_progress_job_id'), 'job_progress', ['job_id'], unique=True)
    op.create_index(op.f('ix_job_progress_user_id'), 'job_progress', ['user_id'], unique=False)
    
    # Create summaries table
    op.create_table('summaries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('summary_text', sa.Text(), nullable=False),
        sa.Column('original_word_count', sa.Integer(), nullable=False),
        sa.Column('summary_word_count', sa.Integer(), nullable=False),
        sa.Column('compression_ratio', sa.Float(), nullable=False),
        sa.Column('processing_time', sa.Float(), nullable=False),
        sa.Column('llm_provider', sa.String(length=50), nullable=False),
        sa.Column('llm_model', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_summaries_created_at'), 'summaries', ['created_at'], unique=False)
    op.create_index('idx_summaries_user_id', 'summaries', ['user_id'], unique=False)
    
    # Create tags table
    op.create_table('tags',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(length=7), nullable=True),
        sa.Column('embedding', Vector(1536), nullable=True),  # Default to OpenAI dimensions, but flexible in practice
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('slug')
    )
    op.create_index(op.f('ix_tags_name'), 'tags', ['name'], unique=True)
    op.create_index(op.f('ix_tags_slug'), 'tags', ['slug'], unique=True)
    
    # Create chat_messages table
    op.create_table('chat_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chat_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_metadata', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['chat_id'], ['chats.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_chat_messages_chat_id', 'chat_messages', ['chat_id'], unique=False)
    
    # Create document_tags association table
    op.create_table('document_tags',
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tag_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('document_id', 'tag_id')
    )
    op.create_index('idx_document_tags_both', 'document_tags', ['document_id', 'tag_id'], unique=False)
    
    # Create folder_tags association table
    op.create_table('folder_tags',
        sa.Column('folder_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tag_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['folder_id'], ['folders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('folder_id', 'tag_id')
    )
    op.create_index('idx_folder_tags_both', 'folder_tags', ['folder_id', 'tag_id'], unique=False)


def downgrade() -> None:
    """Drop all tables in reverse order."""
    # Drop association tables first
    op.drop_index('idx_folder_tags_both', table_name='folder_tags')
    op.drop_table('folder_tags')
    
    op.drop_index('idx_document_tags_both', table_name='document_tags')
    op.drop_table('document_tags')
    
    # Drop dependent tables
    op.drop_index('idx_chat_messages_chat_id', table_name='chat_messages')
    op.drop_table('chat_messages')
    
    op.drop_index(op.f('ix_tags_slug'), table_name='tags')
    op.drop_index(op.f('ix_tags_name'), table_name='tags')
    op.drop_table('tags')
    
    op.drop_index('idx_summaries_user_id', table_name='summaries')
    op.drop_index(op.f('ix_summaries_created_at'), table_name='summaries')
    op.drop_table('summaries')
    
    op.drop_index(op.f('ix_job_progress_user_id'), table_name='job_progress')
    op.drop_index(op.f('ix_job_progress_job_id'), table_name='job_progress')
    op.drop_table('job_progress')
    
    # Drop vector index
    op.execute('DROP INDEX IF EXISTS idx_document_chunks_embedding_vector')
    
    op.drop_index('idx_document_chunks_document_id', table_name='document_chunks')
    op.drop_table('document_chunks')
    
    op.drop_index('idx_chats_user_id_document_id', table_name='chats')
    op.drop_table('chats')
    
    # Drop documents and related indexes
    op.drop_index('idx_documents_deleted_at_null', table_name='documents')
    op.drop_index('idx_documents_folder_id_user_id', table_name='documents')
    op.drop_index('idx_documents_user_id', table_name='documents')
    op.drop_index(op.f('ix_documents_folder_id'), table_name='documents')
    op.drop_index(op.f('ix_documents_file_hash'), table_name='documents')
    op.drop_index(op.f('ix_documents_created_at'), table_name='documents')
    op.drop_index(op.f('ix_documents_archived_at'), table_name='documents')
    op.drop_table('documents')
    
    # Drop folders and related indexes
    op.drop_index('idx_folders_deleted_at_null', table_name='folders')
    op.drop_index(op.f('ix_folders_archived_at'), table_name='folders')
    op.drop_table('folders')
    
    # Drop users
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS documentstatus')
    
    # Drop extensions
    op.execute('DROP EXTENSION IF EXISTS vector')