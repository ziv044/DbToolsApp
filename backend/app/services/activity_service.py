"""Activity log service for tracking events and actions."""
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..models.tenant import ActivityLog


class ActivityService:
    """Service for managing activity log entries."""

    def __init__(self, session: Session):
        self.session = session

    def log(
        self,
        action: str,
        entity_type: str | None = None,
        entity_id: str | None = None,
        details: dict | None = None,
    ) -> ActivityLog:
        """Log an activity entry.

        Args:
            action: The action performed (e.g., 'server_added', 'alert_triggered')
            entity_type: The type of entity (e.g., 'server', 'alert', 'job')
            entity_id: The ID of the entity
            details: Additional details as a dictionary

        Returns:
            The created ActivityLog entry
        """
        entry = ActivityLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
        )
        self.session.add(entry)
        self.session.commit()
        return entry

    def log_batch(
        self,
        entries: list[dict],
    ) -> list[ActivityLog]:
        """Log multiple activity entries at once.

        Args:
            entries: List of dicts with action, entity_type, entity_id, details

        Returns:
            List of created ActivityLog entries
        """
        logs = []
        for entry_data in entries:
            entry = ActivityLog(
                action=entry_data['action'],
                entity_type=entry_data.get('entity_type'),
                entity_id=entry_data.get('entity_id'),
                details=entry_data.get('details'),
            )
            self.session.add(entry)
            logs.append(entry)
        self.session.commit()
        return logs

    def get_activities(
        self,
        action: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        search: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ActivityLog], int]:
        """Get activity log entries with optional filters.

        Args:
            action: Filter by action type
            entity_type: Filter by entity type
            entity_id: Filter by entity ID
            search: Search in action, entity_type, or details
            start_date: Filter entries after this date
            end_date: Filter entries before this date
            limit: Maximum entries to return
            offset: Number of entries to skip

        Returns:
            Tuple of (entries list, total count)
        """
        query = self.session.query(ActivityLog)

        # Apply filters
        if action:
            query = query.filter(ActivityLog.action == action)

        if entity_type:
            query = query.filter(ActivityLog.entity_type == entity_type)

        if entity_id:
            query = query.filter(ActivityLog.entity_id == entity_id)

        if start_date:
            query = query.filter(ActivityLog.created_at >= start_date)

        if end_date:
            query = query.filter(ActivityLog.created_at <= end_date)

        if search:
            search_filter = or_(
                ActivityLog.action.ilike(f'%{search}%'),
                ActivityLog.entity_type.ilike(f'%{search}%'),
                ActivityLog.details.cast(str).ilike(f'%{search}%'),
            )
            query = query.filter(search_filter)

        # Get total count before pagination
        total = query.count()

        # Apply ordering and pagination
        entries = (
            query
            .order_by(ActivityLog.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return entries, total

    def get_activity(self, activity_id: str) -> Optional[ActivityLog]:
        """Get a single activity entry by ID."""
        return (
            self.session.query(ActivityLog)
            .filter(ActivityLog.id == activity_id)
            .first()
        )

    def get_entity_activities(
        self,
        entity_type: str,
        entity_id: str,
        limit: int = 20,
    ) -> list[ActivityLog]:
        """Get activities for a specific entity.

        Args:
            entity_type: The type of entity
            entity_id: The ID of the entity
            limit: Maximum entries to return

        Returns:
            List of ActivityLog entries
        """
        return (
            self.session.query(ActivityLog)
            .filter(
                ActivityLog.entity_type == entity_type,
                ActivityLog.entity_id == entity_id,
            )
            .order_by(ActivityLog.created_at.desc())
            .limit(limit)
            .all()
        )

    def cleanup_old_entries(self, retention_days: int = 90) -> int:
        """Delete activity entries older than retention period.

        Args:
            retention_days: Number of days to retain (default 90)

        Returns:
            Number of deleted entries
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)

        deleted = (
            self.session.query(ActivityLog)
            .filter(ActivityLog.created_at < cutoff)
            .delete(synchronize_session=False)
        )

        self.session.commit()
        return deleted

    def get_action_types(self) -> list[str]:
        """Get distinct action types in the log."""
        result = (
            self.session.query(ActivityLog.action)
            .distinct()
            .order_by(ActivityLog.action)
            .all()
        )
        return [r[0] for r in result if r[0]]

    def get_entity_types(self) -> list[str]:
        """Get distinct entity types in the log."""
        result = (
            self.session.query(ActivityLog.entity_type)
            .distinct()
            .order_by(ActivityLog.entity_type)
            .all()
        )
        return [r[0] for r in result if r[0]]


# Convenience function for logging
def log_activity(
    session: Session,
    action: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    details: dict | None = None,
) -> ActivityLog:
    """Quick function to log an activity entry.

    Args:
        session: Database session
        action: The action performed
        entity_type: The type of entity
        entity_id: The ID of the entity
        details: Additional details

    Returns:
        The created ActivityLog entry
    """
    service = ActivityService(session)
    return service.log(action, entity_type, entity_id, details)
