"""Consolidated initial schema for DocuLearn.

Revision ID: consolidated_initial_schema
Revises: 
Create Date: 2025-01-09 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'consolidated_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables, indexes, and database objects."""
    
    # ========== EXTENSIONS ==========
    # Create required PostgreSQL extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')
    
    # ========== ENUM TYPES ==========
    # Create custom enum types
    op.execute("CREATE TYPE documentstatus AS ENUM ('pending', 'uploading', 'processing', 'completed', 'failed')")
    
    # ========== TABLES ==========
    
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
    
    # Create folders table
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
    
    # Create documents table with search_vector column
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
        sa.Column('search_vector', postgresql.TSVECTOR(), nullable=True),
        sa.ForeignKeyConstraint(['folder_id'], ['folders.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
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
    
    # Create document_chunks table with search_vector column
    op.create_table('document_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('chunk_text', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('chunk_metadata', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('search_vector', postgresql.TSVECTOR(), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
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
    
    # Create tags table
    op.create_table('tags',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(length=7), nullable=True),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('slug')
    )
    
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
    
    # Create document_tags association table
    op.create_table('document_tags',
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tag_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('document_id', 'tag_id')
    )
    
    # Create folder_tags association table
    op.create_table('folder_tags',
        sa.Column('folder_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tag_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['folder_id'], ['folders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('folder_id', 'tag_id')
    )
    
    # ========== INDEXES ==========
    
    # Users table indexes
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('idx_users_provider_provider_id', 'users', ['provider', 'provider_id'])
    op.create_index('idx_users_email_lower', 'users', [sa.text('lower(email)')])
    
    # Folders table indexes
    op.create_index('ix_folders_archived_at', 'folders', ['archived_at'])
    op.create_index('idx_folders_deleted_at_null', 'folders', ['id'], 
                    postgresql_where=sa.text('archived_at IS NULL'))
    op.create_index('idx_folders_updated_at', 'folders', [sa.text('updated_at DESC')])
    op.create_index('idx_folders_parent_id', 'folders', ['parent_id'],
                    postgresql_where=sa.text('archived_at IS NULL'))
    op.create_index('idx_folders_user_id_parent_id', 'folders', ['user_id', 'parent_id'],
                    postgresql_where=sa.text('archived_at IS NULL'))
    op.create_index('idx_folders_user_id_name', 'folders', ['user_id', 'name'],
                    postgresql_where=sa.text('archived_at IS NULL'))
    op.create_index('idx_folders_user_id_archived_at', 'folders',
                    ['user_id', sa.text('archived_at DESC')],
                    postgresql_where=sa.text('archived_at IS NOT NULL'))
    
    # Documents table indexes
    op.create_index('ix_documents_archived_at', 'documents', ['archived_at'])
    op.create_index('ix_documents_created_at', 'documents', ['created_at'])
    op.create_index('ix_documents_file_hash', 'documents', ['file_hash'])
    op.create_index('ix_documents_folder_id', 'documents', ['folder_id'])
    op.create_index('idx_documents_user_id', 'documents', ['user_id'])
    op.create_index('idx_documents_folder_id_user_id', 'documents', ['folder_id', 'user_id'])
    op.create_index('idx_documents_deleted_at_null', 'documents', ['id'],
                    postgresql_where=sa.text('archived_at IS NULL'))
    op.create_index('idx_documents_status', 'documents', ['status'], 
                    postgresql_where=sa.text('archived_at IS NULL'))
    op.create_index('idx_documents_user_id_status', 'documents', ['user_id', 'status'],
                    postgresql_where=sa.text('archived_at IS NULL'))
    op.create_index('idx_documents_folder_id_created_at', 'documents', 
                    ['folder_id', sa.text('created_at DESC')],
                    postgresql_where=sa.text('archived_at IS NULL'))
    op.create_index('idx_documents_file_hash_user_id', 'documents', ['file_hash', 'user_id'],
                    postgresql_where=sa.text('archived_at IS NULL'))
    op.create_index('idx_documents_updated_at', 'documents', [sa.text('updated_at DESC')])
    op.create_index('idx_documents_processed_at', 'documents', ['processed_at'],
                    postgresql_where=sa.text('processed_at IS NOT NULL'))
    op.create_index('idx_documents_user_id_archived_at', 'documents', 
                    ['user_id', sa.text('archived_at DESC')],
                    postgresql_where=sa.text('archived_at IS NOT NULL'))
    op.create_index('idx_documents_user_folder_archived', 'documents',
                    ['user_id', 'folder_id', 'archived_at'],
                    postgresql_where=sa.text('processed_at IS NOT NULL'))
    op.create_index('idx_documents_user_unfiled', 'documents',
                    ['user_id', 'created_at'],
                    postgresql_where=sa.text('folder_id IS NULL AND archived_at IS NULL'))
    op.create_index('idx_documents_search_covering', 'documents',
                    ['user_id', 'status', 'created_at'],
                    postgresql_include=['filename', 'file_size', 'page_count'])
    op.create_index('idx_documents_user_created_desc', 'documents',
                    ['user_id', sa.text('created_at DESC')],
                    postgresql_where=sa.text("archived_at IS NULL"))
    
    # Full-text search index for documents
    op.create_index('idx_documents_search_vector', 'documents', ['search_vector'],
                    postgresql_using='gin')
    
    # Trigram indexes for documents
    op.create_index('idx_documents_filename_trgm', 'documents', ['filename'],
                    postgresql_using='gin', postgresql_ops={'filename': 'gin_trgm_ops'})
    op.execute("""
        CREATE INDEX idx_documents_extracted_text_trgm 
        ON documents 
        USING gin (extracted_text gin_trgm_ops)
        WHERE extracted_text IS NOT NULL
    """)
    
    # Chats table indexes
    op.create_index('idx_chats_user_id_document_id', 'chats', ['user_id', 'document_id'])
    op.create_index('idx_chats_updated_at', 'chats', [sa.text('updated_at DESC')])
    op.create_index('idx_chats_user_id_updated_at', 'chats', ['user_id', sa.text('updated_at DESC')])
    
    # Document chunks table indexes
    op.create_index('idx_document_chunks_document_id', 'document_chunks', ['document_id'])
    op.create_index('idx_document_chunks_document_id_chunk_index', 'document_chunks',
                    ['document_id', 'chunk_index'])
    
    # Vector indexes for document chunks
    op.execute('CREATE INDEX idx_document_chunks_embedding_vector ON document_chunks USING ivfflat (embedding vector_cosine_ops)')
    op.execute("""
        CREATE INDEX idx_document_chunks_embedding_hnsw 
        ON document_chunks USING hnsw (embedding vector_cosine_ops) 
        WITH (m = 16, ef_construction = 64)
        WHERE embedding IS NOT NULL
    """)
    
    # Full-text search index for chunks
    op.create_index('idx_document_chunks_search_vector', 'document_chunks', ['search_vector'],
                    postgresql_using='gin')
    
    # Hybrid search index
    op.execute("""
        CREATE INDEX idx_chunks_hybrid_search 
        ON document_chunks 
        USING gin(search_vector) 
        WHERE embedding IS NOT NULL;
    """)
    
    # Trigram index for chunks
    op.execute("""
        CREATE INDEX idx_document_chunks_chunk_text_trgm 
        ON document_chunks 
        USING gin (chunk_text gin_trgm_ops)
    """)
    
    # Job progress table indexes
    op.create_index('ix_job_progress_job_id', 'job_progress', ['job_id'], unique=True)
    op.create_index('ix_job_progress_user_id', 'job_progress', ['user_id'])
    op.create_index('idx_job_progress_stage', 'job_progress', ['stage'])
    op.create_index('idx_job_progress_completed_at', 'job_progress', [sa.text('completed_at DESC')],
                    postgresql_where=sa.text('completed_at IS NOT NULL'))
    op.create_index('idx_job_progress_user_id_started_at', 'job_progress',
                    ['user_id', sa.text('started_at DESC')],
                    postgresql_where=sa.text('completed_at IS NULL'))
    
    # Summaries table indexes
    op.create_index('ix_summaries_created_at', 'summaries', ['created_at'])
    op.create_index('idx_summaries_user_id', 'summaries', ['user_id'])
    op.create_index('idx_summaries_document_id', 'summaries', ['document_id'])
    op.create_index('idx_summaries_user_id_created_at', 'summaries', 
                    ['user_id', sa.text('created_at DESC')])
    
    # Tags table indexes
    op.create_index('ix_tags_name', 'tags', ['name'], unique=True)
    op.create_index('ix_tags_slug', 'tags', ['slug'], unique=True)
    
    # Vector index for tags
    op.execute("""
        CREATE INDEX idx_tags_embedding_hnsw 
        ON tags USING hnsw (embedding vector_cosine_ops) 
        WITH (m = 16, ef_construction = 64)
        WHERE embedding IS NOT NULL
    """)
    
    # Trigram index for tags
    op.execute("""
        CREATE INDEX idx_tags_name_trgm 
        ON tags 
        USING gin (name gin_trgm_ops)
    """)
    
    # Chat messages table indexes
    op.create_index('idx_chat_messages_chat_id', 'chat_messages', ['chat_id'])
    op.create_index('idx_chat_messages_chat_id_created_at', 'chat_messages',
                    ['chat_id', sa.text('created_at')])
    
    # Association table indexes
    op.create_index('idx_document_tags_both', 'document_tags', ['document_id', 'tag_id'])
    op.create_index('idx_document_tags_tag_id', 'document_tags', ['tag_id'])
    op.create_index('idx_document_tags_created_at', 'document_tags', [sa.text('created_at DESC')])
    op.create_index('idx_folder_tags_both', 'folder_tags', ['folder_id', 'tag_id'])
    op.create_index('idx_folder_tags_tag_id', 'folder_tags', ['tag_id'])
    op.create_index('idx_folder_tags_created_at', 'folder_tags', [sa.text('created_at DESC')])
    
    # ========== FUNCTIONS AND TRIGGERS ==========
    
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
    
    # Create fuzzy search function
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
    
    # Set default trigram similarity threshold
    op.execute("SET pg_trgm.similarity_threshold = 0.3")
    
    # Add comments to important indexes
    op.execute("""
        COMMENT ON INDEX idx_documents_filename_trgm IS 
        'Trigram index for fuzzy filename search with typo tolerance';
    """)
    
    op.execute("""
        COMMENT ON INDEX idx_documents_extracted_text_trgm IS 
        'Trigram index for fuzzy content search - may be slow to build on large datasets';
    """)


def downgrade() -> None:
    """Drop all database objects in reverse order."""
    
    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS search_documents_fuzzy")
    op.execute('DROP FUNCTION IF EXISTS update_chunk_search_vector()')
    op.execute('DROP FUNCTION IF EXISTS update_document_search_vector()')
    
    # Drop triggers
    op.execute('DROP TRIGGER IF EXISTS update_chunk_search_vector_trigger ON document_chunks')
    op.execute('DROP TRIGGER IF EXISTS update_document_search_vector_trigger ON documents')
    
    # Drop association tables
    op.drop_table('folder_tags')
    op.drop_table('document_tags')
    
    # Drop dependent tables
    op.drop_table('chat_messages')
    op.drop_table('tags')
    op.drop_table('summaries')
    op.drop_table('job_progress')
    op.drop_table('document_chunks')
    op.drop_table('chats')
    op.drop_table('documents')
    op.drop_table('folders')
    op.drop_table('users')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS documentstatus')
    
    # Drop extensions (commented out as they might be used elsewhere)
    # op.execute('DROP EXTENSION IF EXISTS pg_trgm')
    # op.execute('DROP EXTENSION IF EXISTS vector')