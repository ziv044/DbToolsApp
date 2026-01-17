"""Create alert_rules and alerts tables.

Revision ID: 011
Create Date: 2026-01-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade():
    # Create alert_rules table
    op.create_table(
        'alert_rules',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('metric_type', sa.String(50), nullable=False),
        sa.Column('operator', sa.String(10), nullable=False),
        sa.Column('threshold', sa.Numeric(18, 4), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Create alerts table
    op.create_table(
        'alerts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('rule_id', UUID(as_uuid=True), sa.ForeignKey('alert_rules.id', ondelete='CASCADE'), nullable=False),
        sa.Column('server_id', UUID(as_uuid=True), sa.ForeignKey('servers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default="'active'"),
        sa.Column('metric_value', sa.Numeric(18, 4), nullable=True),
        sa.Column('triggered_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('acknowledged_by', sa.String(255), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
    )

    # Create indexes for efficient querying
    op.create_index('ix_alerts_status', 'alerts', ['status'])
    op.create_index('ix_alerts_rule_server', 'alerts', ['rule_id', 'server_id'])
    op.create_index('ix_alerts_triggered_at', 'alerts', ['triggered_at'])


def downgrade():
    op.drop_index('ix_alerts_triggered_at', table_name='alerts')
    op.drop_index('ix_alerts_rule_server', table_name='alerts')
    op.drop_index('ix_alerts_status', table_name='alerts')
    op.drop_table('alerts')
    op.drop_table('alert_rules')
