"""Add query analytics fields to running_query_snapshots.

Adds session context fields (login_name, host_name, program_name) and
blocking_session_id for analytics dashboard breakdowns and blocking chain
visualization.

Revision ID: 014
Create Date: 2026-01-18
"""
from alembic import op
import sqlalchemy as sa

revision = '014'
down_revision = '013'
branch_labels = None
depends_on = None


def upgrade():
    # Add session context columns for analytics breakdowns
    op.add_column('running_query_snapshots',
        sa.Column('login_name', sa.String(128), nullable=True))
    op.add_column('running_query_snapshots',
        sa.Column('host_name', sa.String(128), nullable=True))
    op.add_column('running_query_snapshots',
        sa.Column('program_name', sa.String(128), nullable=True))

    # Add blocking information for blocking chain visualization
    op.add_column('running_query_snapshots',
        sa.Column('blocking_session_id', sa.Integer(), nullable=True))

    # Create indexes for efficient aggregation queries
    op.create_index('ix_running_queries_blocking', 'running_query_snapshots',
        ['server_id', 'blocking_session_id'])
    op.create_index('ix_running_queries_database', 'running_query_snapshots',
        ['server_id', 'database_name'])
    op.create_index('ix_running_queries_login', 'running_query_snapshots',
        ['server_id', 'login_name'])


def downgrade():
    # Drop indexes
    op.drop_index('ix_running_queries_login', 'running_query_snapshots')
    op.drop_index('ix_running_queries_database', 'running_query_snapshots')
    op.drop_index('ix_running_queries_blocking', 'running_query_snapshots')

    # Drop columns
    op.drop_column('running_query_snapshots', 'blocking_session_id')
    op.drop_column('running_query_snapshots', 'program_name')
    op.drop_column('running_query_snapshots', 'host_name')
    op.drop_column('running_query_snapshots', 'login_name')
