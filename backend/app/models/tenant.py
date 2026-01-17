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
