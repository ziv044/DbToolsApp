"""Models for tenant-scoped database tables.

These models are used with tenant database sessions, not the system database.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

# Base for tenant models - used with tenant database sessions
TenantBase = declarative_base()


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

    def to_dict(self, include_password: bool = False) -> dict:
        """Convert server to dictionary representation.

        Args:
            include_password: If True, include encrypted_password field.
                            Should only be True for internal use.
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

        return result

    @property
    def connection_string_display(self) -> str:
        """Get display-friendly connection string (no password)."""
        if self.instance_name:
            return f"{self.hostname}\\{self.instance_name}"
        elif self.port != 1433:
            return f"{self.hostname},{self.port}"
        return self.hostname
