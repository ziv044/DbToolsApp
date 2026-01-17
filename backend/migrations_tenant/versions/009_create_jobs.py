"""Create jobs and job_executions tables.

Revision ID: 009
Create Date: 2026-01-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade():
    # Create jobs table
    op.create_table(
        'jobs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('configuration', JSON(), nullable=False, server_default='{}'),
        sa.Column('schedule_type', sa.String(20), nullable=False),
        sa.Column('schedule_config', JSON(), nullable=False, server_default='{}'),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Create index on next_run_at for scheduler queries
    op.create_index('ix_jobs_next_run_at', 'jobs', ['next_run_at'])

    # Create job_executions table
    op.create_table(
        'job_executions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('job_id', UUID(as_uuid=True), sa.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('server_id', UUID(as_uuid=True), sa.ForeignKey('servers.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default="'pending'"),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('result', JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Create indexes for efficient querying
    op.create_index('ix_job_executions_job_started', 'job_executions', ['job_id', 'started_at'])
    op.create_index('ix_job_executions_status', 'job_executions', ['status'])


def downgrade():
    op.drop_index('ix_job_executions_status', table_name='job_executions')
    op.drop_index('ix_job_executions_job_started', table_name='job_executions')
    op.drop_table('job_executions')
    op.drop_index('ix_jobs_next_run_at', table_name='jobs')
    op.drop_table('jobs')
