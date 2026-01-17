"""Create running_query_snapshots table and extend collection_configs.

Revision ID: 012
Create Date: 2026-01-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '012'
down_revision = '011'
branch_labels = None
depends_on = None


def upgrade():
    # Create running_query_snapshots table
    op.create_table(
        'running_query_snapshots',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('server_id', UUID(as_uuid=True), sa.ForeignKey('servers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('collected_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),

        # Query identification
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('request_id', sa.Integer(), nullable=True),
        sa.Column('database_name', sa.String(128), nullable=True),

        # Query text (the main payload)
        sa.Column('query_text', sa.Text(), nullable=True),

        # Timing
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),

        # Status & waits
        sa.Column('status', sa.String(30), nullable=True),
        sa.Column('wait_type', sa.String(60), nullable=True),
        sa.Column('wait_time_ms', sa.Integer(), nullable=True),

        # Resource usage
        sa.Column('cpu_time_ms', sa.Integer(), nullable=True),
        sa.Column('logical_reads', sa.BigInteger(), nullable=True),
        sa.Column('physical_reads', sa.BigInteger(), nullable=True),
        sa.Column('writes', sa.BigInteger(), nullable=True),
    )

    # Create composite index for efficient time-range queries
    op.create_index('ix_running_queries_server_time', 'running_query_snapshots', ['server_id', 'collected_at'])

    # Create index on collected_at for retention cleanup
    op.create_index('ix_running_queries_collected_at', 'running_query_snapshots', ['collected_at'])

    # Add query collection columns to collection_configs
    op.add_column('collection_configs',
        sa.Column('query_collection_enabled', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('collection_configs',
        sa.Column('query_collection_interval', sa.Integer(), nullable=False, server_default='30'))
    op.add_column('collection_configs',
        sa.Column('query_min_duration_ms', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('collection_configs',
        sa.Column('last_query_collected_at', sa.DateTime(timezone=True), nullable=True))


def downgrade():
    # Remove columns from collection_configs
    op.drop_column('collection_configs', 'last_query_collected_at')
    op.drop_column('collection_configs', 'query_min_duration_ms')
    op.drop_column('collection_configs', 'query_collection_interval')
    op.drop_column('collection_configs', 'query_collection_enabled')

    # Drop running_query_snapshots table
    op.drop_index('ix_running_queries_collected_at', 'running_query_snapshots')
    op.drop_index('ix_running_queries_server_time', 'running_query_snapshots')
    op.drop_table('running_query_snapshots')
