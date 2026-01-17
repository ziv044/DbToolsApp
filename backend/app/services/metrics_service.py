"""Service for querying server metrics."""
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.models.tenant import Server, ServerSnapshot


# Time range definitions in hours
TIME_RANGES = {
    '1h': 1,
    '6h': 6,
    '24h': 24,
    '7d': 168,
    '30d': 720,
}

# Aggregation intervals in minutes for each range
AGGREGATION_INTERVALS = {
    '1h': 1,      # No aggregation for 1 hour
    '6h': 5,      # 5-minute averages
    '24h': 15,    # 15-minute averages
    '7d': 60,     # 1-hour averages
    '30d': 240,   # 4-hour averages
}


class MetricsServiceError(Exception):
    """Base exception for metrics service errors."""
    def __init__(self, message: str, code: str = 'METRICS_ERROR'):
        self.message = message
        self.code = code
        super().__init__(message)


class MetricsService:
    """Service for querying server metrics."""

    def __init__(self, session: Session):
        self.session = session

    def _get_server(self, server_id: UUID) -> Server:
        """Get server by ID, raise error if not found."""
        server = self.session.query(Server).filter(
            Server.id == server_id,
            Server.is_deleted == False
        ).first()

        if not server:
            raise MetricsServiceError(f'Server with id {server_id} not found', 'NOT_FOUND')

        return server

    def get_metrics(
        self,
        server_id: UUID,
        time_range: str = '24h',
        metric: Optional[str] = None
    ) -> dict:
        """
        Get metrics for a server within a time range.

        Args:
            server_id: Server UUID
            time_range: Time range (1h, 6h, 24h, 7d, 30d)
            metric: Specific metric to return (cpu, memory, connections) or None for all

        Returns:
            Dictionary with time series data
        """
        self._get_server(server_id)  # Validate server exists

        # Get time range in hours
        hours = TIME_RANGES.get(time_range, 24)
        start_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        # Query snapshots
        snapshots = self.session.query(ServerSnapshot).filter(
            ServerSnapshot.server_id == server_id,
            ServerSnapshot.collected_at >= start_time
        ).order_by(ServerSnapshot.collected_at).all()

        if not snapshots:
            return {
                'server_id': str(server_id),
                'time_range': time_range,
                'data_points': 0,
                'cpu': [],
                'memory': [],
                'connections': [],
                'batch_requests': [],
            }

        # Build time series
        cpu_data = []
        memory_data = []
        connections_data = []
        batch_requests_data = []

        for snapshot in snapshots:
            time_str = snapshot.collected_at.isoformat()

            if metric is None or metric == 'cpu':
                cpu_data.append({
                    'time': time_str,
                    'value': float(snapshot.cpu_percent) if snapshot.cpu_percent else None
                })

            if metric is None or metric == 'memory':
                memory_data.append({
                    'time': time_str,
                    'value': float(snapshot.memory_percent) if snapshot.memory_percent else None
                })

            if metric is None or metric == 'connections':
                connections_data.append({
                    'time': time_str,
                    'value': snapshot.connection_count
                })

            if metric is None or metric == 'batch_requests':
                batch_requests_data.append({
                    'time': time_str,
                    'value': float(snapshot.batch_requests_sec) if snapshot.batch_requests_sec else None
                })

        result = {
            'server_id': str(server_id),
            'time_range': time_range,
            'data_points': len(snapshots),
        }

        if metric is None or metric == 'cpu':
            result['cpu'] = cpu_data
        if metric is None or metric == 'memory':
            result['memory'] = memory_data
        if metric is None or metric == 'connections':
            result['connections'] = connections_data
        if metric is None or metric == 'batch_requests':
            result['batch_requests'] = batch_requests_data

        return result

    def get_latest_snapshot(self, server_id: UUID) -> Optional[dict]:
        """
        Get the latest snapshot for a server.

        Args:
            server_id: Server UUID

        Returns:
            Latest snapshot as dict or None
        """
        self._get_server(server_id)

        snapshot = self.session.query(ServerSnapshot).filter(
            ServerSnapshot.server_id == server_id
        ).order_by(desc(ServerSnapshot.collected_at)).first()

        if not snapshot:
            return None

        return snapshot.to_dict()

    def get_snapshot_count(self, server_id: UUID, hours: int = 24) -> int:
        """
        Get count of snapshots for a server within time range.

        Args:
            server_id: Server UUID
            hours: Number of hours to look back

        Returns:
            Count of snapshots
        """
        start_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        count = self.session.query(func.count(ServerSnapshot.id)).filter(
            ServerSnapshot.server_id == server_id,
            ServerSnapshot.collected_at >= start_time
        ).scalar()

        return count or 0
