"""Service for querying running query snapshots."""
from datetime import datetime, timezone, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.tenant import Server, RunningQuerySnapshot


# Time range definitions in hours
TIME_RANGES = {
    '1h': 1,
    '6h': 6,
    '24h': 24,
    '7d': 168,
    '30d': 720,
}


class RunningQueriesService:
    """Service for querying running query snapshots."""

    def __init__(self, session: Session):
        self.session = session

    def _get_server(self, server_id: UUID) -> Optional[Server]:
        """Get server by ID, return None if not found."""
        return self.session.query(Server).filter(
            Server.id == server_id,
            Server.is_deleted == False
        ).first()

    def get_running_queries(
        self,
        server_id: UUID,
        time_range: str = '1h',
        limit: int = 100
    ) -> dict:
        """
        Get running query snapshots for a server within a time range.

        Args:
            server_id: Server UUID
            time_range: Time range (1h, 6h, 24h, 7d, 30d)
            limit: Maximum number of records to return

        Returns:
            Dictionary with query snapshots data
        """
        server = self._get_server(server_id)

        # Get time range in hours
        hours = TIME_RANGES.get(time_range, 1)
        start_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        # Query snapshots
        snapshots = self.session.query(RunningQuerySnapshot).filter(
            RunningQuerySnapshot.server_id == server_id,
            RunningQuerySnapshot.collected_at >= start_time
        ).order_by(desc(RunningQuerySnapshot.collected_at)).limit(limit).all()

        return {
            'server_id': str(server_id),
            'server_name': server.name if server else None,
            'time_range': time_range,
            'total': len(snapshots),
            'queries': [q.to_dict() for q in snapshots]
        }

    def get_latest_queries(self, server_id: UUID) -> dict:
        """
        Get the most recent running query snapshots for a server.

        Returns all queries from the most recent collection timestamp.

        Args:
            server_id: Server UUID

        Returns:
            Dictionary with latest query snapshots
        """
        server = self._get_server(server_id)

        # Find the most recent collected_at time
        latest_snapshot = self.session.query(RunningQuerySnapshot).filter(
            RunningQuerySnapshot.server_id == server_id
        ).order_by(desc(RunningQuerySnapshot.collected_at)).first()

        if not latest_snapshot:
            return {
                'server_id': str(server_id),
                'server_name': server.name if server else None,
                'collected_at': None,
                'total': 0,
                'queries': []
            }

        # Get all queries from that collection time
        collected_at = latest_snapshot.collected_at
        snapshots = self.session.query(RunningQuerySnapshot).filter(
            RunningQuerySnapshot.server_id == server_id,
            RunningQuerySnapshot.collected_at == collected_at
        ).order_by(desc(RunningQuerySnapshot.duration_ms)).all()

        return {
            'server_id': str(server_id),
            'server_name': server.name if server else None,
            'collected_at': collected_at.isoformat() if collected_at else None,
            'total': len(snapshots),
            'queries': [q.to_dict() for q in snapshots]
        }

    def get_query_count(self, server_id: UUID, hours: int = 24) -> int:
        """
        Get count of running query snapshots for a server within time range.

        Args:
            server_id: Server UUID
            hours: Number of hours to look back

        Returns:
            Count of snapshots
        """
        start_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        from sqlalchemy import func
        count = self.session.query(func.count(RunningQuerySnapshot.id)).filter(
            RunningQuerySnapshot.server_id == server_id,
            RunningQuerySnapshot.collected_at >= start_time
        ).scalar()

        return count or 0

    def get_all_running_queries(
        self,
        server_id: Optional[UUID] = None,
        time_range: str = '1h',
        limit: int = 500
    ) -> dict:
        """
        Get running query snapshots across all servers or filtered by server.

        Args:
            server_id: Optional server UUID to filter by
            time_range: Time range (1h, 6h, 24h, 7d, 30d)
            limit: Maximum number of records to return

        Returns:
            Dictionary with query snapshots and server info
        """
        hours = TIME_RANGES.get(time_range, 1)
        start_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        # Build base query
        query = self.session.query(RunningQuerySnapshot).filter(
            RunningQuerySnapshot.collected_at >= start_time
        )

        # Filter by server if provided
        if server_id:
            query = query.filter(RunningQuerySnapshot.server_id == server_id)

        # Order and limit
        snapshots = query.order_by(
            desc(RunningQuerySnapshot.collected_at)
        ).limit(limit).all()

        # Get server info for all unique server_ids
        server_ids = list(set(s.server_id for s in snapshots))
        servers = self.session.query(Server).filter(
            Server.id.in_(server_ids),
            Server.is_deleted == False
        ).all() if server_ids else []
        server_map = {s.id: s for s in servers}

        # Build response with server info included
        queries = []
        for snapshot in snapshots:
            data = snapshot.to_dict()
            server = server_map.get(snapshot.server_id)
            data['server_name'] = server.name if server else None
            queries.append(data)

        return {
            'time_range': time_range,
            'server_id': str(server_id) if server_id else None,
            'total': len(snapshots),
            'queries': queries
        }
