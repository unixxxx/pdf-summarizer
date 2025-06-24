"""Add cascade delete to folder children relationship

Revision ID: d8414762858c
Revises: 90afbc27e166
Create Date: 2025-06-12 02:06:16.705427

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd8414762858c'
down_revision: Union[str, None] = '90afbc27e166'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop the existing foreign key constraint
    op.drop_constraint('folders_parent_id_fkey', 'folders', type_='foreignkey')
    
    # Create a new foreign key constraint with CASCADE delete
    op.create_foreign_key(
        'folders_parent_id_fkey',
        'folders',
        'folders',
        ['parent_id'],
        ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the CASCADE constraint
    op.drop_constraint('folders_parent_id_fkey', 'folders', type_='foreignkey')
    
    # Recreate the foreign key without CASCADE
    op.create_foreign_key(
        'folders_parent_id_fkey',
        'folders',
        'folders',
        ['parent_id'],
        ['id']
    )
