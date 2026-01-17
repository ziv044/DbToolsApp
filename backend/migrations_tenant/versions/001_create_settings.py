"""Create settings table

Revision ID: 001
Revises:
Create Date: 2026-01-17

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'settings',
        sa.Column('key', sa.String(100), primary_key=True),
        sa.Column('value', postgresql.JSONB, nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'))
    )


def downgrade():
    op.drop_table('settings')
