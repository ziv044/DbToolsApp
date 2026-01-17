"""Service for managing metrics retention settings."""
from typing import Optional
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.tenant import Setting, ServerSnapshot, Metric


class RetentionError(Exception):
    """Base exception for retention errors."""
    def __init__(self, message: str, code: str = 'RETENTION_ERROR'):
        self.message = message
        self.code = code
        super().__init__(message)


class RetentionValidationError(RetentionError):
    """Raised when validation fails."""
    def __init__(self, message: str, field: Optional[str] = None):
        self.field = field
        super().__init__(message, 'VALIDATION_ERROR')


class RetentionService:
    """Service for metrics retention management."""

    # Retention limits
    MIN_RETENTION_DAYS = 1
    MAX_RETENTION_DAYS = 365
    DEFAULT_RETENTION_DAYS = 30

    def __init__(self, session: Session):
        self.session = session

    def get_retention_days(self) -> int:
        """
        Get the current retention period in days.

        Returns:
            Number of days to retain metrics
        """
        setting = self.session.query(Setting).filter_by(
            key=Setting.KEY_RETENTION_DAYS
        ).first()

        if setting:
            return setting.value

        return self.DEFAULT_RETENTION_DAYS

    def set_retention_days(self, days: int) -> int:
        """
        Set the retention period in days.

        Args:
            days: Number of days to retain metrics (1-365)

        Returns:
            Updated retention days value
        """
        # Validate bounds
        if days < self.MIN_RETENTION_DAYS:
            raise RetentionValidationError(
                f'Retention period must be at least {self.MIN_RETENTION_DAYS} day',
                'retention_days'
            )
        if days > self.MAX_RETENTION_DAYS:
            raise RetentionValidationError(
                f'Retention period must not exceed {self.MAX_RETENTION_DAYS} days',
                'retention_days'
            )

        setting = self.session.query(Setting).filter_by(
            key=Setting.KEY_RETENTION_DAYS
        ).first()

        if setting:
            setting.value = days
        else:
            setting = Setting(key=Setting.KEY_RETENTION_DAYS, value=days)
            self.session.add(setting)

        self.session.commit()
        return days

    def get_retention_config(self) -> dict:
        """
        Get the full retention configuration.

        Returns:
            Dictionary with retention settings
        """
        return {
            'retention_days': self.get_retention_days(),
            'min_retention_days': self.MIN_RETENTION_DAYS,
            'max_retention_days': self.MAX_RETENTION_DAYS,
        }

    def get_metrics_stats(self) -> dict:
        """
        Get storage statistics for metrics.

        Returns:
            Dictionary with row counts and date ranges
        """
        # Count snapshots
        snapshot_count = self.session.query(func.count(ServerSnapshot.id)).scalar() or 0

        # Get snapshot date range
        snapshot_date_range = self.session.query(
            func.min(ServerSnapshot.collected_at),
            func.max(ServerSnapshot.collected_at)
        ).first()

        # Count metrics
        metric_count = self.session.query(func.count(Metric.id)).scalar() or 0

        # Get metric date range
        metric_date_range = self.session.query(
            func.min(Metric.collected_at),
            func.max(Metric.collected_at)
        ).first()

        # Get per-server snapshot counts
        server_snapshot_counts = self.session.query(
            ServerSnapshot.server_id,
            func.count(ServerSnapshot.id).label('count')
        ).group_by(ServerSnapshot.server_id).all()

        return {
            'snapshots': {
                'total_count': snapshot_count,
                'oldest': snapshot_date_range[0].isoformat() if snapshot_date_range[0] else None,
                'newest': snapshot_date_range[1].isoformat() if snapshot_date_range[1] else None,
            },
            'metrics': {
                'total_count': metric_count,
                'oldest': metric_date_range[0].isoformat() if metric_date_range[0] else None,
                'newest': metric_date_range[1].isoformat() if metric_date_range[1] else None,
            },
            'servers_with_data': len(server_snapshot_counts),
            'retention_days': self.get_retention_days(),
        }
