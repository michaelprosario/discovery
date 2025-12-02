"""add created_by to all tables

Revision ID: add_created_by_001
Revises: 91f6c7ffafc4
Create Date: 2025-12-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_created_by_001'
down_revision: Union[str, Sequence[str], None] = '91f6c7ffafc4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add created_by column to all tables."""
    # Add created_by column to notebooks table
    op.add_column('notebooks',
        sa.Column('created_by', sa.String(255), nullable=False, server_default='system@discovery.local')
    )
    op.create_index('ix_notebooks_created_by', 'notebooks', ['created_by'])

    # Add created_by column to sources table
    op.add_column('sources',
        sa.Column('created_by', sa.String(255), nullable=False, server_default='system@discovery.local')
    )
    op.create_index('ix_sources_created_by', 'sources', ['created_by'])

    # Add created_by column to outputs table
    op.add_column('outputs',
        sa.Column('created_by', sa.String(255), nullable=False, server_default='system@discovery.local')
    )
    op.create_index('ix_outputs_created_by', 'outputs', ['created_by'])

    # Remove server defaults after backfilling existing data
    op.alter_column('notebooks', 'created_by', server_default=None)
    op.alter_column('sources', 'created_by', server_default=None)
    op.alter_column('outputs', 'created_by', server_default=None)


def downgrade() -> None:
    """Downgrade schema - remove created_by columns."""
    # Remove created_by columns
    op.drop_index('ix_outputs_created_by', 'outputs')
    op.drop_column('outputs', 'created_by')

    op.drop_index('ix_sources_created_by', 'sources')
    op.drop_column('sources', 'created_by')

    op.drop_index('ix_notebooks_created_by', 'notebooks')
    op.drop_column('notebooks', 'created_by')
