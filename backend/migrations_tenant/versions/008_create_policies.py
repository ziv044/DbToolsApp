"""Create policies and policy_versions tables.

Revision ID: 008
Create Date: 2026-01-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade():
    # Create policies table
    op.create_table(
        'policies',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('configuration', JSON(), nullable=False, server_default='{}'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Create policy_versions table
    op.create_table(
        'policy_versions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('policy_id', UUID(as_uuid=True), sa.ForeignKey('policies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('configuration', JSON(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Create unique index on policy_id + version
    op.create_index(
        'ix_policy_versions_policy_version',
        'policy_versions',
        ['policy_id', 'version'],
        unique=True
    )


def downgrade():
    op.drop_index('ix_policy_versions_policy_version', table_name='policy_versions')
    op.drop_table('policy_versions')
    op.drop_table('policies')
