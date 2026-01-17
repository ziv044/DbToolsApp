"""Service for managing collection configurations."""
from uuid import UUID
from typing import Optional

from sqlalchemy.orm import Session

from app.models.tenant import CollectionConfig, Server


class CollectionConfigError(Exception):
    """Base exception for collection config errors."""
    def __init__(self, message: str, code: str = 'CONFIG_ERROR'):
        self.message = message
        self.code = code
        super().__init__(message)


class CollectionConfigNotFoundError(CollectionConfigError):
    """Raised when collection config is not found."""
    def __init__(self, server_id: UUID):
        super().__init__(f'Collection config for server {server_id} not found', 'NOT_FOUND')


class CollectionConfigValidationError(CollectionConfigError):
    """Raised when validation fails."""
    def __init__(self, message: str, field: Optional[str] = None):
        self.field = field
        super().__init__(message, 'VALIDATION_ERROR')


class CollectionConfigService:
    """Service for collection configuration management."""

    def __init__(self, session: Session):
        self.session = session

    def _get_server(self, server_id: UUID) -> Server:
        """Get server by ID, raise error if not found."""
        server = self.session.query(Server).filter(
            Server.id == server_id,
            Server.is_deleted == False
        ).first()

        if not server:
            raise CollectionConfigError(f'Server with id {server_id} not found', 'SERVER_NOT_FOUND')

        return server

    def get_config(self, server_id: UUID) -> CollectionConfig:
        """
        Get collection config for a server.

        Creates default config if it doesn't exist.
        """
        self._get_server(server_id)  # Validate server exists

        config = self.session.query(CollectionConfig).filter_by(server_id=server_id).first()

        if not config:
            # Auto-create default config
            config = CollectionConfig(
                server_id=server_id,
                interval_seconds=CollectionConfig.DEFAULT_INTERVAL,
                enabled=False,
                metrics_enabled=CollectionConfig.DEFAULT_METRICS.copy()
            )
            self.session.add(config)
            self.session.commit()

        return config

    def update_config(
        self,
        server_id: UUID,
        interval_seconds: Optional[int] = None,
        enabled: Optional[bool] = None,
        metrics_enabled: Optional[list] = None
    ) -> CollectionConfig:
        """
        Update collection config for a server.

        Args:
            server_id: Server ID
            interval_seconds: Collection interval (30-3600 seconds)
            enabled: Enable/disable collection
            metrics_enabled: List of metric names to collect

        Returns:
            Updated CollectionConfig
        """
        config = self.get_config(server_id)

        # Validate and update interval
        if interval_seconds is not None:
            if interval_seconds < CollectionConfig.MIN_INTERVAL:
                raise CollectionConfigValidationError(
                    f'Interval must be at least {CollectionConfig.MIN_INTERVAL} seconds',
                    'interval_seconds'
                )
            if interval_seconds > CollectionConfig.MAX_INTERVAL:
                raise CollectionConfigValidationError(
                    f'Interval must not exceed {CollectionConfig.MAX_INTERVAL} seconds',
                    'interval_seconds'
                )
            config.interval_seconds = interval_seconds

        # Update enabled status
        if enabled is not None:
            config.enabled = enabled

        # Validate and update metrics
        if metrics_enabled is not None:
            if not isinstance(metrics_enabled, list):
                raise CollectionConfigValidationError(
                    'metrics_enabled must be a list',
                    'metrics_enabled'
                )
            # Validate metric names (basic check - could validate against MetricType)
            for metric in metrics_enabled:
                if not isinstance(metric, str):
                    raise CollectionConfigValidationError(
                        'All metric names must be strings',
                        'metrics_enabled'
                    )
            config.metrics_enabled = metrics_enabled

        self.session.commit()
        return config

    def start_collection(self, server_id: UUID) -> CollectionConfig:
        """Enable collection for a server."""
        config = self.get_config(server_id)
        config.enabled = True
        self.session.commit()
        return config

    def stop_collection(self, server_id: UUID) -> CollectionConfig:
        """Disable collection for a server."""
        config = self.get_config(server_id)
        config.enabled = False
        self.session.commit()
        return config

    def get_enabled_servers(self) -> list[CollectionConfig]:
        """Get all servers with collection enabled."""
        return self.session.query(CollectionConfig).filter(
            CollectionConfig.enabled == True
        ).all()

    def create_config_for_server(self, server_id: UUID) -> CollectionConfig:
        """Create default config for a new server."""
        config = CollectionConfig(
            server_id=server_id,
            interval_seconds=CollectionConfig.DEFAULT_INTERVAL,
            enabled=False,
            metrics_enabled=CollectionConfig.DEFAULT_METRICS.copy()
        )
        self.session.add(config)
        self.session.commit()
        return config
