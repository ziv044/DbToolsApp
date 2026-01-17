"""Create activity_log table

Revision ID: 002
Revises: 001
Create Date: 2026-01-17

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'activity_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('entity_type', sa.String(50)),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True)),
        sa.Column('details', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'))
    )

    op.create_index('ix_activity_log_created_at', 'activity_log', ['created_at'], postgresql_using='btree')
    op.create_index('ix_activity_log_entity', 'activity_log', ['entity_type', 'entity_id'], postgresql_using='btree')


def downgrade():
    op.drop_index('ix_activity_log_entity')
    op.drop_index('ix_activity_log_created_at')
    op.drop_table('activity_log')
