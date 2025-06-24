"""Replace document_folders many-to-many with direct folder_id on documents

Revision ID: 7c3698d02762
Revises: 0144fc779998
Create Date: 2025-06-12 14:50:26.071430

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7c3698d02762'
down_revision: Union[str, None] = '0144fc779998'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add the new folder_id column first
    op.add_column('documents', sa.Column('folder_id', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_documents_folder_id'), 'documents', ['folder_id'], unique=False)
    op.create_foreign_key('fk_documents_folder_id', 'documents', 'folders', ['folder_id'], ['id'])
    
    # Migrate data from document_folders to documents.folder_id
    # Since documents can only be in one folder now, we'll take the first folder for any document
    op.execute("""
        UPDATE documents d
        SET folder_id = df.folder_id
        FROM (
            SELECT DISTINCT ON (document_id) document_id, folder_id
            FROM document_folders
            ORDER BY document_id, created_at DESC
        ) df
        WHERE d.id = df.document_id
    """)
    
    # Now drop the old table
    op.drop_table('document_folders')


def downgrade() -> None:
    """Downgrade schema."""
    # Recreate the document_folders table
    op.create_table('document_folders',
        sa.Column('document_id', sa.UUID(), autoincrement=False, nullable=False),
        sa.Column('folder_id', sa.UUID(), autoincrement=False, nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], name='document_folders_document_id_fkey', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['folder_id'], ['folders.id'], name='document_folders_folder_id_fkey', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('document_id', 'folder_id', name='document_folders_pkey')
    )
    
    # Migrate data back from documents.folder_id to document_folders
    op.execute("""
        INSERT INTO document_folders (document_id, folder_id, created_at)
        SELECT id, folder_id, CURRENT_TIMESTAMP
        FROM documents
        WHERE folder_id IS NOT NULL
    """)
    
    # Drop the folder_id column
    op.drop_constraint('fk_documents_folder_id', 'documents', type_='foreignkey')
    op.drop_index(op.f('ix_documents_folder_id'), table_name='documents')
    op.drop_column('documents', 'folder_id')
