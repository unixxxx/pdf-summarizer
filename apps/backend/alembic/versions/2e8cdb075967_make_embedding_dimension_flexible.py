"""make embedding dimension flexible

Revision ID: 2e8cdb075967
Revises: c142041b5ea0
Create Date: 2025-06-06 23:41:30.746876

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2e8cdb075967'
down_revision: Union[str, None] = 'c142041b5ea0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop the old column with fixed dimension
    op.drop_column('document_chunks', 'embedding')
    
    # Add new column with flexible dimension
    op.execute('ALTER TABLE document_chunks ADD COLUMN embedding vector')


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the flexible dimension column
    op.drop_column('document_chunks', 'embedding')
    
    # Add back the fixed dimension column
    op.execute('ALTER TABLE document_chunks ADD COLUMN embedding vector(1536)')
