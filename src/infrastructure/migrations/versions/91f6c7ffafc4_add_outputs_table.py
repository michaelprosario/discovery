"""add_outputs_table

Revision ID: 91f6c7ffafc4
Revises: 913390ba554c
Create Date: 2025-11-04 04:24:58.557895

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '91f6c7ffafc4'
down_revision: Union[str, Sequence[str], None] = '913390ba554c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - create outputs table."""
    # Create outputs table
    op.create_table(
        'outputs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('notebook_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('content', sa.Text(), nullable=False, server_default=''),
        sa.Column('output_type', sa.String(length=50), nullable=False, server_default='blog_post'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('prompt', sa.Text(), nullable=True),
        sa.Column('template_name', sa.String(length=100), nullable=True),
        sa.Column('output_metadata', postgresql.JSON(), nullable=False, server_default='{}'),
        sa.Column('source_references', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'),
        sa.Column('word_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['notebook_id'], ['notebooks.id'], ondelete='CASCADE'),
    )

    # Create indexes on outputs table
    op.create_index('ix_outputs_notebook_id', 'outputs', ['notebook_id'])
    op.create_index('ix_outputs_status', 'outputs', ['status'])
    op.create_index('ix_outputs_output_type', 'outputs', ['output_type'])
    op.create_index('ix_outputs_created_at', 'outputs', ['created_at'])
    op.create_index('ix_outputs_updated_at', 'outputs', ['updated_at'])
    op.create_index('ix_outputs_completed_at', 'outputs', ['completed_at'])

    # Create composite index for filtering by notebook and status
    op.create_index(
        'ix_outputs_notebook_status',
        'outputs',
        ['notebook_id', 'status'],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema - drop outputs table."""
    # Drop outputs table
    op.drop_index('ix_outputs_notebook_status', table_name='outputs')
    op.drop_index('ix_outputs_completed_at', table_name='outputs')
    op.drop_index('ix_outputs_updated_at', table_name='outputs')
    op.drop_index('ix_outputs_created_at', table_name='outputs')
    op.drop_index('ix_outputs_output_type', table_name='outputs')
    op.drop_index('ix_outputs_status', table_name='outputs')
    op.drop_index('ix_outputs_notebook_id', table_name='outputs')
    op.drop_table('outputs')
