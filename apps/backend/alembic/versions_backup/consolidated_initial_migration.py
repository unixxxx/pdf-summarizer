"""Consolidated initial migration - complete schema

Revision ID: consolidated_initial
Revises: 
Create Date: 2025-06-14 00:00:00.000000

This is a consolidated migration that creates the complete database schema
from scratch. It represents the final state of all migrations combined.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'consolidated_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create complete database schema."""
    
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('picture', sa.String(length=500), nullable=True),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('provider_id', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider', 'provider_id', name='_provider_user_uc')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # Create tags table
    op.create_table('tags',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(length=7), nullable=True),
        sa.Column('embedding', Vector(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tags_name'), 'tags', ['name'], unique=True)
    op.create_index(op.f('ix_tags_slug'), 'tags', ['slug'], unique=True)
    
    # Create folders table with self-referential relationship
    op.create_table('folders',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(length=7), nullable=True),
        sa.Column('parent_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['parent_id'], ['folders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'name', 'parent_id', name='_user_folder_name_uc')
    )
    op.create_index(op.f('ix_folders_deleted_at'), 'folders', ['deleted_at'], unique=False)
    
    # Create documents table
    op.create_table('documents',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('file_hash', sa.String(length=64), nullable=False),
        sa.Column('page_count', sa.Integer(), nullable=True),
        sa.Column('storage_path', sa.String(length=500), nullable=True),
        sa.Column('extracted_text', sa.Text(), nullable=True),
        sa.Column('word_count', sa.Integer(), nullable=True),
        sa.Column('folder_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['folder_id'], ['folders.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_documents_created_at'), 'documents', ['created_at'], unique=False)
    op.create_index(op.f('ix_documents_file_hash'), 'documents', ['file_hash'], unique=False)
    op.create_index(op.f('ix_documents_folder_id'), 'documents', ['folder_id'], unique=False)
    op.create_index(op.f('ix_documents_deleted_at'), 'documents', ['deleted_at'], unique=False)
    op.create_index('idx_documents_user_id', 'documents', ['user_id'])
    op.create_index('idx_documents_folder_id_user_id', 'documents', ['folder_id', 'user_id'])
    op.create_index('idx_documents_deleted_at_null', 'documents', ['deleted_at'], 
                    postgresql_where=sa.text('deleted_at IS NULL'))
    
    # Create chats table
    op.create_table('chats',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_chats_user_id_document_id', 'chats', ['user_id', 'document_id'])
    
    # Create document_chunks table
    op.create_table('document_chunks',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('chunk_text', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(), nullable=True),
        sa.Column('chunk_metadata', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_document_chunks_document_id', 'document_chunks', ['document_id'])
    
    # Create summaries table
    op.create_table('summaries',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('summary_text', sa.Text(), nullable=False),
        sa.Column('original_word_count', sa.Integer(), nullable=False),
        sa.Column('summary_word_count', sa.Integer(), nullable=False),
        sa.Column('compression_ratio', sa.Float(), nullable=False),
        sa.Column('processing_time', sa.Float(), nullable=False),
        sa.Column('llm_provider', sa.String(length=50), nullable=False),
        sa.Column('llm_model', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_summaries_created_at'), 'summaries', ['created_at'], unique=False)
    op.create_index('idx_summaries_user_id', 'summaries', ['user_id'])
    
    # Create chat_messages table
    op.create_table('chat_messages',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('chat_id', sa.UUID(), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_metadata', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['chat_id'], ['chats.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_chat_messages_chat_id', 'chat_messages', ['chat_id'])
    
    # Create association tables
    
    # document_tags association table
    op.create_table('document_tags',
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('tag_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('document_id', 'tag_id')
    )
    op.create_index('idx_document_tags_both', 'document_tags', ['document_id', 'tag_id'])
    
    # folder_tags association table (for smart folders)
    op.create_table('folder_tags',
        sa.Column('folder_id', sa.UUID(), nullable=False),
        sa.Column('tag_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['folder_id'], ['folders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('folder_id', 'tag_id')
    )
    op.create_index('idx_folder_tags_both', 'folder_tags', ['folder_id', 'tag_id'])
    
    # Create partial index for folders soft delete
    op.create_index('idx_folders_deleted_at_null', 'folders', ['deleted_at'],
                    postgresql_where=sa.text('deleted_at IS NULL'))
    
    # Create helper function for HNSW indexes
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


def downgrade() -> None:
    """Drop complete database schema."""
    # Drop helper function
    op.execute("DROP FUNCTION IF EXISTS create_hnsw_indexes_if_needed();")
    
    # Drop association tables first
    op.drop_table('folder_tags')
    op.drop_table('document_tags')
    
    # Drop dependent tables
    op.drop_table('chat_messages')
    op.drop_table('summaries')
    op.drop_table('document_chunks')
    op.drop_table('chats')
    op.drop_table('documents')
    op.drop_table('folders')
    
    # Drop independent tables
    op.drop_index(op.f('ix_tags_slug'), table_name='tags')
    op.drop_index(op.f('ix_tags_name'), table_name='tags')
    op.drop_table('tags')
    
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    
    # Disable extension (optional - might want to keep it)
    # op.execute('DROP EXTENSION IF EXISTS vector')