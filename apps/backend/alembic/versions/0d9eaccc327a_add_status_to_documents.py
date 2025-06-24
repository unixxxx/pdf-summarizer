"""add_status_to_documents

Revision ID: 0d9eaccc327a
Revises: consolidated_initial
Create Date: 2025-06-18 01:05:37.218019

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0d9eaccc327a'
down_revision: Union[str, None] = 'consolidated_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create enum type
    document_status_enum = sa.Enum('pending', 'uploading', 'processing', 'completed', 'failed', name='documentstatus')
    document_status_enum.create(op.get_bind())
    
    # Add status column with default value
    op.add_column('documents', sa.Column('status', document_status_enum, nullable=False, server_default='pending'))
    
    # Create index on status for faster filtering
    op.create_index(op.f('ix_documents_status'), 'documents', ['status'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop index
    op.drop_index(op.f('ix_documents_status'), table_name='documents')
    
    # Drop column
    op.drop_column('documents', 'status')
    
    # Drop enum type
    document_status_enum = sa.Enum(name='documentstatus')
    document_status_enum.drop(op.get_bind())
