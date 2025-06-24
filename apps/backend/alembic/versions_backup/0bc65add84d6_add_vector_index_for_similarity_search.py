"""add vector index for similarity search

Revision ID: 0bc65add84d6
Revises: 2e8cdb075967
Create Date: 2025-06-07 00:17:50.275469

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0bc65add84d6'
down_revision: Union[str, None] = '2e8cdb075967'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add indexes for fast similarity search."""
    # Create index on document_id for filtered searches
    # This is the most important index for our use case
    op.create_index(
        'idx_document_chunks_document_id',
        'document_chunks',
        ['document_id'],
        if_not_exists=True
    )
    
    # Note: Vector indexes require fixed dimensions in pgvector < 0.5.0
    # Since we're using flexible dimensions, we rely on PostgreSQL's
    # efficient sequential scan with our document_id filter reducing the search space


def downgrade() -> None:
    """Remove indexes."""
    op.drop_index('idx_document_chunks_document_id', 'document_chunks', if_exists=True)
