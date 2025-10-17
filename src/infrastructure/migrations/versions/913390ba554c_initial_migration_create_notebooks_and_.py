"""Initial migration: create notebooks and sources tables

Revision ID: 913390ba554c
Revises:
Create Date: 2025-10-17 06:18:46.379874

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '913390ba554c'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - create notebooks and sources tables."""
    # Create notebooks table
    op.create_table(
        'notebooks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('source_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('output_count', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_notebooks_name')
    )

    # Create index on notebooks.name for faster lookups
    op.create_index('ix_notebooks_name', 'notebooks', ['name'])
    op.create_index('ix_notebooks_created_at', 'notebooks', ['created_at'])

    # Create sources table
    op.create_table(
        'sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('notebook_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=500), nullable=False),
        sa.Column('source_type', sa.String(length=20), nullable=False),
        sa.Column('file_type', sa.String(length=20), nullable=True),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('file_path', sa.Text(), nullable=True),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('extracted_text', sa.Text(), nullable=False, server_default=''),
        sa.Column('source_metadata', postgresql.JSON(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['notebook_id'], ['notebooks.id'], ondelete='CASCADE'),
    )

    # Create indexes on sources table
    op.create_index('ix_sources_notebook_id', 'sources', ['notebook_id'])
    op.create_index('ix_sources_content_hash', 'sources', ['content_hash'])
    op.create_index('ix_sources_deleted_at', 'sources', ['deleted_at'])
    op.create_index('ix_sources_created_at', 'sources', ['created_at'])

    # Create composite index for duplicate detection
    op.create_index(
        'ix_sources_notebook_hash',
        'sources',
        ['notebook_id', 'content_hash'],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema - drop sources and notebooks tables."""
    # Drop sources table (must be before notebooks due to foreign key)
    op.drop_index('ix_sources_notebook_hash', table_name='sources')
    op.drop_index('ix_sources_created_at', table_name='sources')
    op.drop_index('ix_sources_deleted_at', table_name='sources')
    op.drop_index('ix_sources_content_hash', table_name='sources')
    op.drop_index('ix_sources_notebook_id', table_name='sources')
    op.drop_table('sources')

    # Drop notebooks table
    op.drop_index('ix_notebooks_created_at', table_name='notebooks')
    op.drop_index('ix_notebooks_name', table_name='notebooks')
    op.drop_table('notebooks')
