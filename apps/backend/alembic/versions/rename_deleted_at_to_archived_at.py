"""rename deleted_at to archived_at

Revision ID: d5a7b8c9f3e2
Revises: 0d9eaccc327a
Create Date: 2025-01-19 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5a7b8c9f3e2'
down_revision: Union[str, None] = '0d9eaccc327a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename deleted_at column to archived_at in documents table
    op.alter_column('documents', 'deleted_at', new_column_name='archived_at')
    
    # Rename deleted_at column to archived_at in folders table
    op.alter_column('folders', 'deleted_at', new_column_name='archived_at')


def downgrade() -> None:
    # Rename archived_at column back to deleted_at in documents table
    op.alter_column('documents', 'archived_at', new_column_name='deleted_at')
    
    # Rename archived_at column back to deleted_at in folders table
    op.alter_column('folders', 'archived_at', new_column_name='deleted_at')