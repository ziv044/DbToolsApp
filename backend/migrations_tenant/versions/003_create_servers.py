"""Create servers table

Revision ID: 003
Revises: 002
Create Date: 2026-01-17

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'servers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('hostname', sa.String(255), nullable=False),
        sa.Column('port', sa.Integer, nullable=False, server_default='1433'),
        sa.Column('instance_name', sa.String(100), nullable=True),
        sa.Column('auth_type', sa.String(20), nullable=False),
        sa.Column('username', sa.String(100), nullable=True),
        sa.Column('encrypted_password', sa.Text, nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='unknown'),
        sa.Column('is_deleted', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('last_checked', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'))
    )

    # Create unique constraint on name (for non-deleted servers)
    op.create_index(
        'ix_servers_name_unique',
        'servers',
        ['name'],
        unique=True,
        postgresql_where=sa.text('is_deleted = false')
    )


def downgrade():
    op.drop_index('ix_servers_name_unique')
    op.drop_table('servers')
