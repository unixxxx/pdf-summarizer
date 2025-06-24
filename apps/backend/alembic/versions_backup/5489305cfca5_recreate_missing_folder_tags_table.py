"""Recreate missing folder_tags table

Revision ID: 5489305cfca5
Revises: 7c3698d02762
Create Date: 2025-06-12 17:52:22.297833

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5489305cfca5'
down_revision: Union[str, None] = '7c3698d02762'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create folder_tags table if it doesn't exist."""
    # Check if table exists first
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    if 'folder_tags' not in tables:
        op.create_table('folder_tags',
            sa.Column('folder_id', sa.UUID(), nullable=False),
            sa.Column('tag_id', sa.UUID(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(['folder_id'], ['folders.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('folder_id', 'tag_id')
        )


def downgrade() -> None:
    """Drop folder_tags table."""
    op.drop_table('folder_tags')