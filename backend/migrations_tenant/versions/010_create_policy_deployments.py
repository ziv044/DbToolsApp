"""Create policy_deployments table.

Revision ID: 010
Create Date: 2026-01-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'policy_deployments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('policy_id', UUID(as_uuid=True), sa.ForeignKey('policies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('policy_version', sa.Integer(), nullable=False),
        sa.Column('group_id', UUID(as_uuid=True), sa.ForeignKey('server_groups.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_id', UUID(as_uuid=True), sa.ForeignKey('jobs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deployed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('deployed_by', sa.String(255), nullable=True),
    )

    # Create unique index - a policy can only be deployed once per group
    op.create_index(
        'ix_policy_deployments_policy_group',
        'policy_deployments',
        ['policy_id', 'group_id'],
        unique=True
    )


def downgrade():
    op.drop_index('ix_policy_deployments_policy_group', table_name='policy_deployments')
    op.drop_table('policy_deployments')
