"""Add query collection filter columns to collection_configs.

Revision ID: 013
Create Date: 2026-01-17
"""
from alembic import op
import sqlalchemy as sa

revision = '013'
down_revision = '012'
branch_labels = None
depends_on = None


def upgrade():
    # Add query filter columns to collection_configs
    op.add_column('collection_configs',
        sa.Column('query_filter_database', sa.String(128), nullable=True))
    op.add_column('collection_configs',
        sa.Column('query_filter_login', sa.String(128), nullable=True))
    op.add_column('collection_configs',
        sa.Column('query_filter_user', sa.String(128), nullable=True))
    op.add_column('collection_configs',
        sa.Column('query_filter_text_include', sa.Text(), nullable=True))
    op.add_column('collection_configs',
        sa.Column('query_filter_text_exclude', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('collection_configs', 'query_filter_text_exclude')
    op.drop_column('collection_configs', 'query_filter_text_include')
    op.drop_column('collection_configs', 'query_filter_user')
    op.drop_column('collection_configs', 'query_filter_login')
    op.drop_column('collection_configs', 'query_filter_database')
