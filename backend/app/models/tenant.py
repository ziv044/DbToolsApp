"""Models for tenant-scoped database tables.

These models are used with tenant database sessions, not the system database.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, Table, ForeignKey, Index, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSON, JSONB
from sqlalchemy.orm import declarative_base, relationship

# Base for tenant models - used with tenant database sessions
TenantBase = declarative_base()

# Association table for many-to-many relationship between servers and groups
server_group_members = Table(
    'server_group_members',
    TenantBase.metadata,
    Column('server_id', UUID(as_uuid=True), ForeignKey('servers.id'), primary_key=True),
    Column('group_id', UUID(as_uuid=True), ForeignKey('server_groups.id'), primary_key=True),
    Column('added_at', DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
)

# Association table for many-to-many relationship between servers and labels
server_labels = Table(
    'server_labels',
    TenantBase.metadata,
    Column('server_id', UUID(as_uuid=True), ForeignKey('servers.id'), primary_key=True),
    Column('label_id', UUID(as_uuid=True), ForeignKey('labels.id'), primary_key=True),
    Column('assigned_at', DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
)


def utc_now():
    """Return current UTC time with timezone info."""
    return datetime.now(timezone.utc)


class Server(TenantBase):
    """SQL Server connection configuration."""
    __tablename__ = 'servers'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    hostname = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False, default=1433)
    instance_name = Column(String(100), nullable=True)
    auth_type = Column(String(20), nullable=False)  # 'sql' or 'windows'
    username = Column(String(100), nullable=True)
    encrypted_password = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default='unknown')
    is_deleted = Column(Boolean, nullable=False, default=False)
    last_checked = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    # Valid auth types
    AUTH_TYPE_SQL = 'sql'
    AUTH_TYPE_WINDOWS = 'windows'
    VALID_AUTH_TYPES = [AUTH_TYPE_SQL, AUTH_TYPE_WINDOWS]

    # Valid statuses
    STATUS_UNKNOWN = 'unknown'
    STATUS_ONLINE = 'online'
    STATUS_OFFLINE = 'offline'
    STATUS_ERROR = 'error'

    def to_dict(self, include_password: bool = False, include_labels: bool = False) -> dict:
        """Convert server to dictionary representation.

        Args:
            include_password: If True, include encrypted_password field.
                            Should only be True for internal use.
            include_labels: If True, include labels list.
        """
        result = {
            'id': str(self.id),
            'name': self.name,
            'hostname': self.hostname,
            'port': self.port,
            'instance_name': self.instance_name,
            'auth_type': self.auth_type,
            'username': self.username,
            'status': self.status,
            'last_checked': self.last_checked.isoformat() if self.last_checked else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_password:
            result['encrypted_password'] = self.encrypted_password

        if include_labels:
            result['labels'] = [label.to_dict() for label in self.labels]

        return result

    @property
    def connection_string_display(self) -> str:
        """Get display-friendly connection string (no password)."""
        if self.instance_name:
            return f"{self.hostname}\\{self.instance_name}"
        elif self.port != 1433:
            return f"{self.hostname},{self.port}"
        return self.hostname

    # Relationship to groups (populated after ServerGroup is defined)
    groups = relationship(
        'ServerGroup',
        secondary=server_group_members,
        back_populates='servers'
    )

    # Relationship to labels
    labels = relationship(
        'Label',
        secondary=server_labels,
        back_populates='servers'
    )


class ServerGroup(TenantBase):
    """Server group for organizing servers."""
    __tablename__ = 'server_groups'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)  # Hex color like #FF5733
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    # Relationship to servers
    servers = relationship(
        'Server',
        secondary=server_group_members,
        back_populates='groups'
    )

    def to_dict(self, include_servers: bool = False) -> dict:
        """Convert group to dictionary representation."""
        result = {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_servers:
            result['servers'] = [
                {'id': str(s.id), 'name': s.name, 'status': s.status}
                for s in self.servers if not s.is_deleted
            ]
        else:
            result['member_count'] = len([s for s in self.servers if not s.is_deleted])

        return result


class Label(TenantBase):
    """Label/tag for categorizing servers."""
    __tablename__ = 'labels'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), nullable=False, unique=True)
    color = Column(String(7), nullable=True, default='#6B7280')  # Default gray color
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    # Relationship to servers
    servers = relationship(
        'Server',
        secondary=server_labels,
        back_populates='labels'
    )

    def to_dict(self) -> dict:
        """Convert label to dictionary representation."""
        return {
            'id': str(self.id),
            'name': self.name,
            'color': self.color,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class MetricType(TenantBase):
    """Type of metric that can be collected."""
    __tablename__ = 'metric_types'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), nullable=False, unique=True)
    unit = Column(String(20), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    def to_dict(self) -> dict:
        """Convert metric type to dictionary representation."""
        return {
            'id': str(self.id),
            'name': self.name,
            'unit': self.unit,
            'description': self.description,
        }


class ServerSnapshot(TenantBase):
    """Point-in-time snapshot of server metrics."""
    __tablename__ = 'server_snapshots'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    server_id = Column(UUID(as_uuid=True), ForeignKey('servers.id'), nullable=False)
    collected_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    # Core metrics stored as individual columns for efficient querying
    cpu_percent = Column(Numeric(5, 2), nullable=True)
    memory_percent = Column(Numeric(5, 2), nullable=True)
    connection_count = Column(Integer, nullable=True)
    batch_requests_sec = Column(Numeric(10, 2), nullable=True)
    page_life_expectancy = Column(Integer, nullable=True)
    blocked_processes = Column(Integer, nullable=True)

    # Extended metrics stored as JSON for flexibility
    extended_metrics = Column(JSON, nullable=True)

    # Status at time of collection
    status = Column(String(20), nullable=True)

    # Composite index for efficient time-range queries
    __table_args__ = (
        Index('ix_snapshots_server_time', 'server_id', 'collected_at'),
    )

    def to_dict(self) -> dict:
        """Convert snapshot to dictionary representation."""
        return {
            'id': str(self.id),
            'server_id': str(self.server_id),
            'collected_at': self.collected_at.isoformat() if self.collected_at else None,
            'cpu_percent': float(self.cpu_percent) if self.cpu_percent else None,
            'memory_percent': float(self.memory_percent) if self.memory_percent else None,
            'connection_count': self.connection_count,
            'batch_requests_sec': float(self.batch_requests_sec) if self.batch_requests_sec else None,
            'page_life_expectancy': self.page_life_expectancy,
            'blocked_processes': self.blocked_processes,
            'extended_metrics': self.extended_metrics,
            'status': self.status,
        }


class Metric(TenantBase):
    """Individual metric data point (for detailed historical data)."""
    __tablename__ = 'metrics'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    server_id = Column(UUID(as_uuid=True), ForeignKey('servers.id'), nullable=False)
    metric_type_id = Column(UUID(as_uuid=True), ForeignKey('metric_types.id'), nullable=False)
    value = Column(Numeric(18, 4), nullable=False)
    collected_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    # Composite index for efficient time-range queries by server and metric type
    __table_args__ = (
        Index('ix_metrics_server_time', 'server_id', 'collected_at'),
        Index('ix_metrics_server_type_time', 'server_id', 'metric_type_id', 'collected_at'),
    )

    def to_dict(self) -> dict:
        """Convert metric to dictionary representation."""
        return {
            'id': str(self.id),
            'server_id': str(self.server_id),
            'metric_type_id': str(self.metric_type_id),
            'value': float(self.value),
            'collected_at': self.collected_at.isoformat() if self.collected_at else None,
        }


class Setting(TenantBase):
    """Tenant-specific settings stored as key-value pairs."""
    __tablename__ = 'settings'

    key = Column(String(100), primary_key=True)
    value = Column(JSONB, nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    # Default settings keys
    KEY_RETENTION_DAYS = 'metrics_retention_days'

    @classmethod
    def get_default_settings(cls) -> dict:
        """Get default settings values."""
        return {
            cls.KEY_RETENTION_DAYS: 30,
        }

    def to_dict(self) -> dict:
        """Convert setting to dictionary representation."""
        return {
            'key': self.key,
            'value': self.value,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class CollectionConfig(TenantBase):
    """Collection configuration for a server."""
    __tablename__ = 'collection_configs'

    server_id = Column(UUID(as_uuid=True), ForeignKey('servers.id', ondelete='CASCADE'), primary_key=True)
    interval_seconds = Column(Integer, nullable=False, default=60)
    enabled = Column(Boolean, nullable=False, default=False)
    metrics_enabled = Column(JSON, nullable=False, default=['cpu_percent', 'memory_percent', 'connection_count'])
    last_collected_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    # Validation constants
    MIN_INTERVAL = 30
    MAX_INTERVAL = 3600
    DEFAULT_INTERVAL = 60
    DEFAULT_METRICS = ['cpu_percent', 'memory_percent', 'connection_count']

    def to_dict(self) -> dict:
        """Convert config to dictionary representation."""
        return {
            'server_id': str(self.server_id),
            'interval_seconds': self.interval_seconds,
            'enabled': self.enabled,
            'metrics_enabled': self.metrics_enabled,
            'last_collected_at': self.last_collected_at.isoformat() if self.last_collected_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class Policy(TenantBase):
    """Reusable policy configuration for SQL Server operations."""
    __tablename__ = 'policies'

    # Policy types
    TYPE_BACKUP = 'backup'
    TYPE_INDEX_MAINTENANCE = 'index_maintenance'
    TYPE_INTEGRITY_CHECK = 'integrity_check'
    TYPE_CUSTOM_SCRIPT = 'custom_script'
    VALID_TYPES = [TYPE_BACKUP, TYPE_INDEX_MAINTENANCE, TYPE_INTEGRITY_CHECK, TYPE_CUSTOM_SCRIPT]

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    configuration = Column(JSON, nullable=False, default=dict)
    version = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, nullable=False, default=True)
    is_deleted = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    # Relationship to version history
    versions = relationship('PolicyVersion', back_populates='policy', order_by='desc(PolicyVersion.version)')

    def to_dict(self, include_versions: bool = False) -> dict:
        """Convert policy to dictionary representation."""
        result = {
            'id': str(self.id),
            'name': self.name,
            'type': self.type,
            'description': self.description,
            'configuration': self.configuration,
            'version': self.version,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_versions:
            result['versions'] = [v.to_dict() for v in self.versions]

        return result


class PolicyVersion(TenantBase):
    """Historical version of a policy configuration (immutable versioning)."""
    __tablename__ = 'policy_versions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id = Column(UUID(as_uuid=True), ForeignKey('policies.id', ondelete='CASCADE'), nullable=False)
    version = Column(Integer, nullable=False)
    configuration = Column(JSON, nullable=False)
    description = Column(Text, nullable=True)  # Description at time of this version
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    # Composite unique constraint on policy_id + version
    __table_args__ = (
        Index('ix_policy_versions_policy_version', 'policy_id', 'version', unique=True),
    )

    # Relationship back to policy
    policy = relationship('Policy', back_populates='versions')

    def to_dict(self) -> dict:
        """Convert policy version to dictionary representation."""
        return {
            'id': str(self.id),
            'policy_id': str(self.policy_id),
            'version': self.version,
            'configuration': self.configuration,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Job(TenantBase):
    """Scheduled job for executing policies or custom scripts."""
    __tablename__ = 'jobs'

    # Schedule types
    SCHEDULE_ONCE = 'once'
    SCHEDULE_INTERVAL = 'interval'
    SCHEDULE_CRON = 'cron'
    SCHEDULE_EVENT_TRIGGERED = 'event_triggered'
    VALID_SCHEDULE_TYPES = [SCHEDULE_ONCE, SCHEDULE_INTERVAL, SCHEDULE_CRON, SCHEDULE_EVENT_TRIGGERED]

    # Job types
    TYPE_POLICY_EXECUTION = 'policy_execution'
    TYPE_DATA_COLLECTION = 'data_collection'
    TYPE_CUSTOM_SCRIPT = 'custom_script'
    TYPE_ALERT_CHECK = 'alert_check'
    VALID_JOB_TYPES = [TYPE_POLICY_EXECUTION, TYPE_DATA_COLLECTION, TYPE_CUSTOM_SCRIPT, TYPE_ALERT_CHECK]

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    configuration = Column(JSON, nullable=False, default=dict)
    schedule_type = Column(String(20), nullable=False)
    schedule_config = Column(JSON, nullable=False, default=dict)
    is_enabled = Column(Boolean, nullable=False, default=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True, index=True)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    # Relationship to executions
    executions = relationship('JobExecution', back_populates='job', order_by='desc(JobExecution.started_at)')

    def to_dict(self, include_executions: bool = False) -> dict:
        """Convert job to dictionary representation."""
        result = {
            'id': str(self.id),
            'name': self.name,
            'type': self.type,
            'configuration': self.configuration,
            'schedule_type': self.schedule_type,
            'schedule_config': self.schedule_config,
            'is_enabled': self.is_enabled,
            'next_run_at': self.next_run_at.isoformat() if self.next_run_at else None,
            'last_run_at': self.last_run_at.isoformat() if self.last_run_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_executions:
            result['executions'] = [e.to_dict() for e in self.executions[:10]]  # Limit to recent 10

        return result


class JobExecution(TenantBase):
    """Execution record for a scheduled job."""
    __tablename__ = 'job_executions'

    # Execution statuses
    STATUS_PENDING = 'pending'
    STATUS_RUNNING = 'running'
    STATUS_SUCCESS = 'success'
    STATUS_FAILED = 'failed'
    STATUS_CANCELLED = 'cancelled'
    VALID_STATUSES = [STATUS_PENDING, STATUS_RUNNING, STATUS_SUCCESS, STATUS_FAILED, STATUS_CANCELLED]

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False)
    server_id = Column(UUID(as_uuid=True), ForeignKey('servers.id', ondelete='SET NULL'), nullable=True)
    status = Column(String(20), nullable=False, default=STATUS_PENDING)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    # Indexes for efficient querying
    __table_args__ = (
        Index('ix_job_executions_job_started', 'job_id', 'started_at'),
        Index('ix_job_executions_status', 'status'),
    )

    # Relationships
    job = relationship('Job', back_populates='executions')
    server = relationship('Server')

    def to_dict(self, include_job: bool = False, include_server: bool = False) -> dict:
        """Convert execution to dictionary representation."""
        result = {
            'id': str(self.id),
            'job_id': str(self.job_id),
            'server_id': str(self.server_id) if self.server_id else None,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'result': self.result,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        if include_job and self.job:
            result['job'] = {
                'name': self.job.name,
                'type': self.job.type,
            }

        if include_server and self.server:
            result['server'] = {
                'name': self.server.name,
                'hostname': self.server.hostname,
            }

        return result

    @property
    def duration_seconds(self) -> float | None:
        """Calculate execution duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class PolicyDeployment(TenantBase):
    """Deployment of a policy to a server group."""
    __tablename__ = 'policy_deployments'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id = Column(UUID(as_uuid=True), ForeignKey('policies.id', ondelete='CASCADE'), nullable=False)
    policy_version = Column(Integer, nullable=False)
    group_id = Column(UUID(as_uuid=True), ForeignKey('server_groups.id', ondelete='CASCADE'), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey('jobs.id', ondelete='SET NULL'), nullable=True)  # Linked scheduler job
    deployed_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    deployed_by = Column(String(255), nullable=True)  # User who deployed

    # Composite unique constraint - a policy can only be deployed once per group
    __table_args__ = (
        Index('ix_policy_deployments_policy_group', 'policy_id', 'group_id', unique=True),
    )

    # Relationships
    policy = relationship('Policy', backref='deployments')
    group = relationship('ServerGroup', backref='policy_deployments')
    job = relationship('Job', backref='policy_deployments')

    def to_dict(self, include_policy: bool = False, include_group: bool = False) -> dict:
        """Convert deployment to dictionary representation."""
        result = {
            'id': str(self.id),
            'policy_id': str(self.policy_id),
            'policy_version': self.policy_version,
            'group_id': str(self.group_id),
            'job_id': str(self.job_id) if self.job_id else None,
            'deployed_at': self.deployed_at.isoformat() if self.deployed_at else None,
            'deployed_by': self.deployed_by,
        }

        if include_policy and self.policy:
            result['policy'] = {
                'name': self.policy.name,
                'type': self.policy.type,
                'is_active': self.policy.is_active,
            }

        if include_group and self.group:
            result['group'] = {
                'name': self.group.name,
                'color': self.group.color,
            }

        return result


class AlertRule(TenantBase):
    """Alert rule for monitoring metrics and triggering alerts."""
    __tablename__ = 'alert_rules'

    # Operators
    OP_GT = 'gt'  # Greater than
    OP_GTE = 'gte'  # Greater than or equal
    OP_LT = 'lt'  # Less than
    OP_LTE = 'lte'  # Less than or equal
    OP_EQ = 'eq'  # Equal
    VALID_OPERATORS = [OP_GT, OP_GTE, OP_LT, OP_LTE, OP_EQ]

    # Severity levels
    SEVERITY_INFO = 'info'
    SEVERITY_WARNING = 'warning'
    SEVERITY_CRITICAL = 'critical'
    VALID_SEVERITIES = [SEVERITY_INFO, SEVERITY_WARNING, SEVERITY_CRITICAL]

    # Metric types that can be monitored
    VALID_METRIC_TYPES = [
        'cpu_percent', 'memory_percent', 'connection_count',
        'batch_requests_sec', 'page_life_expectancy', 'blocked_processes',
    ]

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    metric_type = Column(String(50), nullable=False)
    operator = Column(String(10), nullable=False)  # gt, gte, lt, lte, eq
    threshold = Column(Numeric(18, 4), nullable=False)
    severity = Column(String(20), nullable=False)  # info, warning, critical
    is_enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    # Relationship to alerts
    alerts = relationship('Alert', back_populates='rule', cascade='all, delete-orphan')

    def to_dict(self) -> dict:
        """Convert alert rule to dictionary representation."""
        return {
            'id': str(self.id),
            'name': self.name,
            'metric_type': self.metric_type,
            'operator': self.operator,
            'threshold': float(self.threshold),
            'severity': self.severity,
            'is_enabled': self.is_enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def evaluate(self, value: float) -> bool:
        """Evaluate if the given value triggers this alert rule."""
        threshold = float(self.threshold)
        if self.operator == self.OP_GT:
            return value > threshold
        elif self.operator == self.OP_GTE:
            return value >= threshold
        elif self.operator == self.OP_LT:
            return value < threshold
        elif self.operator == self.OP_LTE:
            return value <= threshold
        elif self.operator == self.OP_EQ:
            return value == threshold
        return False


class Alert(TenantBase):
    """Alert instance triggered by an alert rule."""
    __tablename__ = 'alerts'

    # Alert statuses
    STATUS_ACTIVE = 'active'
    STATUS_ACKNOWLEDGED = 'acknowledged'
    STATUS_RESOLVED = 'resolved'
    VALID_STATUSES = [STATUS_ACTIVE, STATUS_ACKNOWLEDGED, STATUS_RESOLVED]

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id = Column(UUID(as_uuid=True), ForeignKey('alert_rules.id', ondelete='CASCADE'), nullable=False)
    server_id = Column(UUID(as_uuid=True), ForeignKey('servers.id', ondelete='CASCADE'), nullable=False)
    status = Column(String(20), nullable=False, default=STATUS_ACTIVE)
    metric_value = Column(Numeric(18, 4), nullable=True)  # Value that triggered the alert
    triggered_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(String(255), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)

    # Indexes for efficient querying
    __table_args__ = (
        Index('ix_alerts_status', 'status'),
        Index('ix_alerts_rule_server', 'rule_id', 'server_id'),
        Index('ix_alerts_triggered_at', 'triggered_at'),
    )

    # Relationships
    rule = relationship('AlertRule', back_populates='alerts')
    server = relationship('Server')

    def to_dict(self, include_rule: bool = False, include_server: bool = False) -> dict:
        """Convert alert to dictionary representation."""
        result = {
            'id': str(self.id),
            'rule_id': str(self.rule_id),
            'server_id': str(self.server_id),
            'status': self.status,
            'metric_value': float(self.metric_value) if self.metric_value else None,
            'triggered_at': self.triggered_at.isoformat() if self.triggered_at else None,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'acknowledged_by': self.acknowledged_by,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'notes': self.notes,
        }

        if include_rule and self.rule:
            result['rule'] = {
                'name': self.rule.name,
                'metric_type': self.rule.metric_type,
                'operator': self.rule.operator,
                'threshold': float(self.rule.threshold),
                'severity': self.rule.severity,
            }

        if include_server and self.server:
            result['server'] = {
                'id': str(self.server.id),
                'name': self.server.name,
                'hostname': self.server.hostname,
            }

        return result


class ActivityLog(TenantBase):
    """Activity log for tracking important events and actions."""
    __tablename__ = 'activity_log'

    # Action types
    ACTION_ALERT_TRIGGERED = 'alert_triggered'
    ACTION_ALERT_RESOLVED = 'alert_resolved'
    ACTION_ALERT_ACKNOWLEDGED = 'alert_acknowledged'
    ACTION_JOB_EXECUTED = 'job_executed'
    ACTION_JOB_FAILED = 'job_failed'
    ACTION_POLICY_DEPLOYED = 'policy_deployed'
    ACTION_SERVER_ONLINE = 'server_online'
    ACTION_SERVER_OFFLINE = 'server_offline'

    # Entity types
    ENTITY_ALERT = 'alert'
    ENTITY_JOB = 'job'
    ENTITY_POLICY = 'policy'
    ENTITY_SERVER = 'server'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    details = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    # Indexes for efficient querying
    __table_args__ = (
        Index('ix_activity_log_created_at', 'created_at'),
        Index('ix_activity_log_entity', 'entity_type', 'entity_id'),
    )

    def to_dict(self) -> dict:
        """Convert activity log to dictionary representation."""
        return {
            'id': str(self.id),
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': str(self.entity_id) if self.entity_id else None,
            'details': self.details,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


# Seed data for metric types
METRIC_TYPES_SEED = [
    ('cpu_percent', '%', 'SQL Server CPU utilization percentage'),
    ('memory_percent', '%', 'SQL Server memory utilization percentage'),
    ('connection_count', 'count', 'Number of active connections'),
    ('batch_requests_sec', 'req/s', 'Batch requests per second'),
    ('page_life_expectancy', 'sec', 'Page life expectancy in seconds'),
    ('blocked_processes', 'count', 'Number of blocked processes'),
    ('disk_io_reads', 'reads/s', 'Disk I/O reads per second'),
    ('disk_io_writes', 'writes/s', 'Disk I/O writes per second'),
    ('wait_time_ms', 'ms', 'Total wait time in milliseconds'),
]
