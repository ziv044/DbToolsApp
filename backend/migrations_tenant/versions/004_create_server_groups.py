"""Create server_groups and server_group_members tables.

Revision ID: 004
Create Date: 2026-01-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # Create server_groups table
    op.create_table(
        'server_groups',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('color', sa.String(7), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Create server_group_members junction table
    op.create_table(
        'server_group_members',
        sa.Column('server_id', UUID(as_uuid=True), sa.ForeignKey('servers.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('group_id', UUID(as_uuid=True), sa.ForeignKey('server_groups.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('added_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Create index on server_group_members for faster lookups
    op.create_index('ix_server_group_members_server_id', 'server_group_members', ['server_id'])
    op.create_index('ix_server_group_members_group_id', 'server_group_members', ['group_id'])


def downgrade():
    op.drop_index('ix_server_group_members_group_id', 'server_group_members')
    op.drop_index('ix_server_group_members_server_id', 'server_group_members')
    op.drop_table('server_group_members')
    op.drop_table('server_groups')
