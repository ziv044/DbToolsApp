"""Create labels and server_labels tables.

Revision ID: 005
Create Date: 2026-01-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    # Create labels table
    op.create_table(
        'labels',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(50), nullable=False, unique=True),
        sa.Column('color', sa.String(7), nullable=True, server_default='#6B7280'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Create index on label name for faster lookups
    op.create_index('ix_labels_name', 'labels', ['name'])

    # Create server_labels junction table
    op.create_table(
        'server_labels',
        sa.Column('server_id', UUID(as_uuid=True), sa.ForeignKey('servers.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('label_id', UUID(as_uuid=True), sa.ForeignKey('labels.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Create indexes on server_labels for faster lookups
    op.create_index('ix_server_labels_server_id', 'server_labels', ['server_id'])
    op.create_index('ix_server_labels_label_id', 'server_labels', ['label_id'])


def downgrade():
    op.drop_index('ix_server_labels_label_id', 'server_labels')
    op.drop_index('ix_server_labels_server_id', 'server_labels')
    op.drop_table('server_labels')
    op.drop_index('ix_labels_name', 'labels')
    op.drop_table('labels')
