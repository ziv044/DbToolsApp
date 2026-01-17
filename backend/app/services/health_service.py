"""Service for calculating server health status."""
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from uuid import UUID

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.tenant import Server, ServerSnapshot, Setting, CollectionConfig


class HealthStatus:
    """Health status constants."""
    HEALTHY = 'healthy'
    WARNING = 'warning'
    CRITICAL = 'critical'
    OFFLINE = 'offline'
    UNKNOWN = 'unknown'


class HealthThresholds:
    """Default health thresholds."""
    CPU_WARNING = 80
    CPU_CRITICAL = 95
    MEMORY_WARNING = 85
    MEMORY_CRITICAL = 95
    OFFLINE_SECONDS = 300  # 5 minutes


# Setting keys for configurable thresholds
SETTING_CPU_WARNING = 'health_cpu_warning'
SETTING_CPU_CRITICAL = 'health_cpu_critical'
SETTING_MEMORY_WARNING = 'health_memory_warning'
SETTING_MEMORY_CRITICAL = 'health_memory_critical'
SETTING_OFFLINE_SECONDS = 'health_offline_seconds'


class HealthService:
    """Service for server health calculations."""

    def __init__(self, session: Session):
        self.session = session
        self._thresholds = None

    def _get_thresholds(self) -> dict:
        """Get health thresholds from settings or use defaults."""
        if self._thresholds is None:
            self._thresholds = {
                'cpu_warning': self._get_setting(SETTING_CPU_WARNING, HealthThresholds.CPU_WARNING),
                'cpu_critical': self._get_setting(SETTING_CPU_CRITICAL, HealthThresholds.CPU_CRITICAL),
                'memory_warning': self._get_setting(SETTING_MEMORY_WARNING, HealthThresholds.MEMORY_WARNING),
                'memory_critical': self._get_setting(SETTING_MEMORY_CRITICAL, HealthThresholds.MEMORY_CRITICAL),
                'offline_seconds': self._get_setting(SETTING_OFFLINE_SECONDS, HealthThresholds.OFFLINE_SECONDS),
            }
        return self._thresholds

    def _get_setting(self, key: str, default):
        """Get a setting value or return default."""
        setting = self.session.query(Setting).filter_by(key=key).first()
        if setting:
            return setting.value
        return default

    def calculate_health(
        self,
        server: Server,
        latest_snapshot: Optional[ServerSnapshot],
        collection_config: Optional[CollectionConfig] = None
    ) -> str:
        """
        Calculate health status for a server.

        Args:
            server: Server model instance
            latest_snapshot: Most recent snapshot or None
            collection_config: Collection config for the server

        Returns:
            Health status string: healthy, warning, critical, offline, unknown
        """
        thresholds = self._get_thresholds()

        # Unknown if collection is disabled or never collected
        if collection_config and not collection_config.enabled:
            return HealthStatus.UNKNOWN

        if not latest_snapshot:
            return HealthStatus.UNKNOWN

        # Check if data is stale (offline)
        now = datetime.now(timezone.utc)
        if latest_snapshot.collected_at:
            # Handle timezone-naive datetime
            collected_at = latest_snapshot.collected_at
            if collected_at.tzinfo is None:
                collected_at = collected_at.replace(tzinfo=timezone.utc)

            seconds_since_collection = (now - collected_at).total_seconds()
            if seconds_since_collection > thresholds['offline_seconds']:
                return HealthStatus.OFFLINE

        # Check if server status indicates offline
        if latest_snapshot.status == 'offline' or server.status == 'offline':
            return HealthStatus.OFFLINE

        # Check CPU and memory thresholds
        cpu = float(latest_snapshot.cpu_percent) if latest_snapshot.cpu_percent else 0
        memory = float(latest_snapshot.memory_percent) if latest_snapshot.memory_percent else 0

        # Critical takes precedence
        if cpu > thresholds['cpu_critical'] or memory > thresholds['memory_critical']:
            return HealthStatus.CRITICAL

        # Then warning
        if cpu > thresholds['cpu_warning'] or memory > thresholds['memory_warning']:
            return HealthStatus.WARNING

        return HealthStatus.HEALTHY

    def get_server_health(self, server_id: UUID) -> dict:
        """
        Get health status for a single server.

        Args:
            server_id: Server UUID

        Returns:
            Health status dict or None if server not found
        """
        server = self.session.query(Server).filter(
            Server.id == server_id,
            Server.is_deleted == False
        ).first()

        if not server:
            return None

        # Get latest snapshot
        latest_snapshot = self.session.query(ServerSnapshot).filter(
            ServerSnapshot.server_id == server_id
        ).order_by(desc(ServerSnapshot.collected_at)).first()

        # Get collection config
        collection_config = self.session.query(CollectionConfig).filter_by(
            server_id=server_id
        ).first()

        health_status = self.calculate_health(server, latest_snapshot, collection_config)

        return {
            'server_id': str(server.id),
            'name': server.name,
            'hostname': server.hostname,
            'status': health_status,
            'last_collected_at': latest_snapshot.collected_at.isoformat() if latest_snapshot and latest_snapshot.collected_at else None,
            'cpu_percent': float(latest_snapshot.cpu_percent) if latest_snapshot and latest_snapshot.cpu_percent else None,
            'memory_percent': float(latest_snapshot.memory_percent) if latest_snapshot and latest_snapshot.memory_percent else None,
            'connection_count': latest_snapshot.connection_count if latest_snapshot else None,
            'collection_enabled': collection_config.enabled if collection_config else False,
        }

    def get_all_servers_health(self) -> List[dict]:
        """
        Get health status for all servers.

        Returns:
            List of health status dicts
        """
        servers = self.session.query(Server).filter(
            Server.is_deleted == False
        ).all()

        results = []
        for server in servers:
            health = self.get_server_health(server.id)
            if health:
                results.append(health)

        return results

    def get_thresholds(self) -> dict:
        """
        Get current health thresholds.

        Returns:
            Dictionary of threshold settings
        """
        return self._get_thresholds()

    def update_thresholds(
        self,
        cpu_warning: Optional[int] = None,
        cpu_critical: Optional[int] = None,
        memory_warning: Optional[int] = None,
        memory_critical: Optional[int] = None,
        offline_seconds: Optional[int] = None
    ) -> dict:
        """
        Update health thresholds.

        Args:
            cpu_warning: CPU warning threshold (%)
            cpu_critical: CPU critical threshold (%)
            memory_warning: Memory warning threshold (%)
            memory_critical: Memory critical threshold (%)
            offline_seconds: Seconds before marking as offline

        Returns:
            Updated thresholds
        """
        updates = {}

        if cpu_warning is not None:
            if not (0 < cpu_warning < 100):
                raise ValueError('cpu_warning must be between 0 and 100')
            updates[SETTING_CPU_WARNING] = cpu_warning

        if cpu_critical is not None:
            if not (0 < cpu_critical <= 100):
                raise ValueError('cpu_critical must be between 0 and 100')
            updates[SETTING_CPU_CRITICAL] = cpu_critical

        if memory_warning is not None:
            if not (0 < memory_warning < 100):
                raise ValueError('memory_warning must be between 0 and 100')
            updates[SETTING_MEMORY_WARNING] = memory_warning

        if memory_critical is not None:
            if not (0 < memory_critical <= 100):
                raise ValueError('memory_critical must be between 0 and 100')
            updates[SETTING_MEMORY_CRITICAL] = memory_critical

        if offline_seconds is not None:
            if not (30 <= offline_seconds <= 3600):
                raise ValueError('offline_seconds must be between 30 and 3600')
            updates[SETTING_OFFLINE_SECONDS] = offline_seconds

        # Apply updates
        for key, value in updates.items():
            setting = self.session.query(Setting).filter_by(key=key).first()
            if setting:
                setting.value = value
            else:
                setting = Setting(key=key, value=value)
                self.session.add(setting)

        self.session.commit()

        # Clear cached thresholds
        self._thresholds = None

        return self._get_thresholds()
