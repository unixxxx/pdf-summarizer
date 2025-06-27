"""Fix cascade deletes for document relationships

Revision ID: fix_cascade_deletes
Revises: a9132ced46c7
Create Date: 2024-01-27 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fix_cascade_deletes'
down_revision = 'a9132ced46c7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if constraint already has CASCADE
    connection = op.get_bind()
    
    # Get existing foreign key constraints
    result = connection.execute(sa.text("""
        SELECT 
            tc.constraint_name,
            tc.table_name,
            rc.delete_rule
        FROM 
            information_schema.table_constraints AS tc 
            JOIN information_schema.referential_constraints AS rc 
                ON tc.constraint_name = rc.constraint_name
        WHERE 
            tc.constraint_type = 'FOREIGN KEY' AND
            tc.table_name IN ('document_chunks', 'summaries', 'chats', 'job_progress') AND
            rc.constraint_schema = current_schema()
    """))
    
    constraints_to_update = []
    for row in result:
        if row[2] != 'CASCADE':
            constraints_to_update.append((row[0], row[1]))
    
    # Update document_chunks
    if any(c[1] == 'document_chunks' for c in constraints_to_update):
        op.drop_constraint('document_chunks_document_id_fkey', 'document_chunks', type_='foreignkey')
        op.create_foreign_key(
            'document_chunks_document_id_fkey',
            'document_chunks',
            'documents',
            ['document_id'],
            ['id'],
            ondelete='CASCADE'
        )
    
    # Update job_progress if it exists
    if any(c[1] == 'job_progress' for c in constraints_to_update):
        op.drop_constraint('job_progress_document_id_fkey', 'job_progress', type_='foreignkey')
        op.create_foreign_key(
            'job_progress_document_id_fkey',
            'job_progress',
            'documents',
            ['document_id'],
            ['id'],
            ondelete='CASCADE'
        )
    
    # Update summaries if it exists
    if any(c[1] == 'summaries' for c in constraints_to_update):
        op.drop_constraint('summaries_document_id_fkey', 'summaries', type_='foreignkey')
        op.create_foreign_key(
            'summaries_document_id_fkey',
            'summaries',
            'documents',
            ['document_id'],
            ['id'],
            ondelete='CASCADE'
        )
    
    # Update chats if it exists
    if any(c[1] == 'chats' for c in constraints_to_update):
        op.drop_constraint('chats_document_id_fkey', 'chats', type_='foreignkey')
        op.create_foreign_key(
            'chats_document_id_fkey',
            'chats',
            'documents',
            ['document_id'],
            ['id'],
            ondelete='CASCADE'
        )


def downgrade() -> None:
    # Revert to non-cascading foreign keys
    # Note: This will fail if there are orphaned records
    
    # document_chunks
    op.drop_constraint('document_chunks_document_id_fkey', 'document_chunks', type_='foreignkey')
    op.create_foreign_key(
        'document_chunks_document_id_fkey',
        'document_chunks',
        'documents',
        ['document_id'],
        ['id']
    )
    
    # Try to update other tables if they exist
    connection = op.get_bind()
    
    # Check which tables exist
    result = connection.execute(sa.text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = current_schema() 
        AND table_name IN ('job_progress', 'summaries', 'chats')
    """))
    
    existing_tables = [row[0] for row in result]
    
    if 'job_progress' in existing_tables:
        op.drop_constraint('job_progress_document_id_fkey', 'job_progress', type_='foreignkey')
        op.create_foreign_key(
            'job_progress_document_id_fkey',
            'job_progress',
            'documents',
            ['document_id'],
            ['id']
        )
    
    if 'summaries' in existing_tables:
        op.drop_constraint('summaries_document_id_fkey', 'summaries', type_='foreignkey')
        op.create_foreign_key(
            'summaries_document_id_fkey',
            'summaries',
            'documents',
            ['document_id'],
            ['id']
        )
    
    if 'chats' in existing_tables:
        op.drop_constraint('chats_document_id_fkey', 'chats', type_='foreignkey')
        op.create_foreign_key(
            'chats_document_id_fkey',
            'chats',
            'documents',
            ['document_id'],
            ['id']
        )