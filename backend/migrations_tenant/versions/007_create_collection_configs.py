"""Create collection_configs table.

Revision ID: 007
Create Date: 2026-01-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'collection_configs',
        sa.Column('server_id', UUID(as_uuid=True), sa.ForeignKey('servers.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('interval_seconds', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('metrics_enabled', JSON(), nullable=False, server_default='["cpu_percent", "memory_percent", "connection_count"]'),
        sa.Column('last_collected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table('collection_configs')
