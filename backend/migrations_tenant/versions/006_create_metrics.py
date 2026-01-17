"""Create metric_types, server_snapshots, and metrics tables.

Revision ID: 006
Create Date: 2026-01-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    # Create metric_types table
    op.create_table(
        'metric_types',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(50), nullable=False, unique=True),
        sa.Column('unit', sa.String(20), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Create index on metric_types name
    op.create_index('ix_metric_types_name', 'metric_types', ['name'])

    # Create server_snapshots table
    op.create_table(
        'server_snapshots',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('server_id', UUID(as_uuid=True), sa.ForeignKey('servers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('collected_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('cpu_percent', sa.Numeric(5, 2), nullable=True),
        sa.Column('memory_percent', sa.Numeric(5, 2), nullable=True),
        sa.Column('connection_count', sa.Integer(), nullable=True),
        sa.Column('batch_requests_sec', sa.Numeric(10, 2), nullable=True),
        sa.Column('page_life_expectancy', sa.Integer(), nullable=True),
        sa.Column('blocked_processes', sa.Integer(), nullable=True),
        sa.Column('extended_metrics', JSON(), nullable=True),
        sa.Column('status', sa.String(20), nullable=True),
    )

    # Create composite index for efficient time-range queries on snapshots
    op.create_index('ix_snapshots_server_time', 'server_snapshots', ['server_id', 'collected_at'])

    # Create metrics table for detailed individual metric data
    op.create_table(
        'metrics',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('server_id', UUID(as_uuid=True), sa.ForeignKey('servers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('metric_type_id', UUID(as_uuid=True), sa.ForeignKey('metric_types.id', ondelete='CASCADE'), nullable=False),
        sa.Column('value', sa.Numeric(18, 4), nullable=False),
        sa.Column('collected_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Create composite indexes for efficient time-range queries on metrics
    op.create_index('ix_metrics_server_time', 'metrics', ['server_id', 'collected_at'])
    op.create_index('ix_metrics_server_type_time', 'metrics', ['server_id', 'metric_type_id', 'collected_at'])


def downgrade():
    op.drop_index('ix_metrics_server_type_time', 'metrics')
    op.drop_index('ix_metrics_server_time', 'metrics')
    op.drop_table('metrics')
    op.drop_index('ix_snapshots_server_time', 'server_snapshots')
    op.drop_table('server_snapshots')
    op.drop_index('ix_metric_types_name', 'metric_types')
    op.drop_table('metric_types')
