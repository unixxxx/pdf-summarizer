"""add_performance_indexes_comprehensive

Revision ID: 3f9f7f62f929
Revises: 72c667decb3e
Create Date: 2025-06-13 11:20:51.031670

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3f9f7f62f929'
down_revision: Union[str, None] = '72c667decb3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # User query indexes
    op.create_index('idx_documents_user_id', 'documents', ['user_id'])
    op.create_index('idx_summaries_user_id', 'summaries', ['user_id'])
    
    # Composite index for folder queries
    op.create_index('idx_documents_folder_id_user_id', 'documents', ['folder_id', 'user_id'])
    
    # Association table indexes
    op.create_index('idx_document_tags_both', 'document_tags', ['document_id', 'tag_id'])
    op.create_index('idx_folder_tags_both', 'folder_tags', ['folder_id', 'tag_id'])
    
    # Soft delete partial indexes
    op.create_index('idx_documents_deleted_at_null', 'documents', ['deleted_at'], 
                    postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_folders_deleted_at_null', 'folders', ['deleted_at'],
                    postgresql_where=sa.text('deleted_at IS NULL'))
    
    # Additional performance indexes
    op.create_index('idx_document_chunks_document_id', 'document_chunks', ['document_id'])
    op.create_index('idx_chat_messages_chat_id', 'chat_messages', ['chat_id'])
    op.create_index('idx_chats_user_id_document_id', 'chats', ['user_id', 'document_id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop all indexes in reverse order
    op.drop_index('idx_chats_user_id_document_id', table_name='chats')
    op.drop_index('idx_chat_messages_chat_id', table_name='chat_messages')
    op.drop_index('idx_document_chunks_document_id', table_name='document_chunks')
    op.drop_index('idx_folders_deleted_at_null', table_name='folders')
    op.drop_index('idx_documents_deleted_at_null', table_name='documents')
    op.drop_index('idx_folder_tags_both', table_name='folder_tags')
    op.drop_index('idx_document_tags_both', table_name='document_tags')
    op.drop_index('idx_documents_folder_id_user_id', table_name='documents')
    op.drop_index('idx_summaries_user_id', table_name='summaries')
    op.drop_index('idx_documents_user_id', table_name='documents')
