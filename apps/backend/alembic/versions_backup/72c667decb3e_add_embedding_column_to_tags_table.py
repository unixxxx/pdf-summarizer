"""Add embedding column to tags table

Revision ID: 72c667decb3e
Revises: 5489305cfca5
Create Date: 2025-06-12 18:14:35.161633

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '72c667decb3e'
down_revision: Union[str, None] = '5489305cfca5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add embedding column to tags table."""
    # Add embedding column with flexible dimensions
    op.add_column('tags', sa.Column('embedding', Vector(), nullable=True))
    
    # Note: Vector indexes require fixed dimensions
    # We'll rely on sequential scan with filtering for now


def downgrade() -> None:
    """Remove embedding column from tags table."""
    # Drop the column
    op.drop_column('tags', 'embedding')