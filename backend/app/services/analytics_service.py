"""Analytics service for query dashboard data aggregation."""
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy import func, desc, and_, or_, case
from sqlalchemy.orm import Session

from app.models.tenant import RunningQuerySnapshot, Server


class AnalyticsServiceError(Exception):
    """Base exception for analytics service errors."""
    def __init__(self, message: str, code: str = 'ANALYTICS_ERROR'):
        self.message = message
        self.code = code
        super().__init__(message)


class AnalyticsService:
    """Service for query analytics and aggregations."""

    def __init__(self, session: Session):
        self.session = session

    def _validate_server(self, server_id: UUID) -> Server:
        """Validate server exists and return it."""
        server = self.session.query(Server).filter(
            Server.id == server_id,
            Server.is_deleted == False
        ).first()
        if not server:
            raise AnalyticsServiceError('Server not found', 'NOT_FOUND')
        return server

    def _parse_date_range(self, start: Optional[str], end: Optional[str]) -> tuple[datetime, datetime]:
        """Parse date range from ISO strings, default to last 1 hour."""
        now = datetime.now(timezone.utc)
        if end:
            try:
                end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
            except ValueError:
                end_dt = now
        else:
            end_dt = now

        if start:
            try:
                start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            except ValueError:
                start_dt = end_dt - timedelta(hours=1)
        else:
            start_dt = end_dt - timedelta(hours=1)

        # Limit to 30 days max
        if (end_dt - start_dt).days > 30:
            start_dt = end_dt - timedelta(days=30)

        return start_dt, end_dt

    def get_running_queries(self, server_id: UUID) -> Dict[str, Any]:
        """Get currently running queries (latest snapshot)."""
        self._validate_server(server_id)

        # Get the latest collected_at for this server
        latest_time = self.session.query(
            func.max(RunningQuerySnapshot.collected_at)
        ).filter(
            RunningQuerySnapshot.server_id == server_id
        ).scalar()

        if not latest_time:
            return {
                'columns': self._get_query_columns(),
                'rows': [],
                'total_rows': 0,
                'collected_at': None
            }

        # Get all queries from the latest snapshot
        queries = self.session.query(RunningQuerySnapshot).filter(
            RunningQuerySnapshot.server_id == server_id,
            RunningQuerySnapshot.collected_at == latest_time
        ).order_by(desc(RunningQuerySnapshot.duration_ms)).all()

        return {
            'columns': self._get_query_columns(),
            'rows': [q.to_dict() for q in queries],
            'total_rows': len(queries),
            'collected_at': latest_time.isoformat() if latest_time else None
        }

    def _get_query_columns(self) -> List[Dict[str, Any]]:
        """Get column definitions for query table."""
        return [
            {'key': 'session_id', 'label': 'Session', 'sortable': True},
            {'key': 'database_name', 'label': 'Database', 'sortable': True},
            {'key': 'login_name', 'label': 'Login', 'sortable': True},
            {'key': 'duration_ms', 'label': 'Duration (ms)', 'sortable': True},
            {'key': 'cpu_time_ms', 'label': 'CPU (ms)', 'sortable': True},
            {'key': 'status', 'label': 'Status', 'sortable': True},
            {'key': 'wait_type', 'label': 'Wait Type', 'sortable': True},
            {'key': 'blocking_session_id', 'label': 'Blocked By', 'sortable': True},
            {'key': 'query_text', 'label': 'Query', 'sortable': False},
        ]

    def get_blocking_chains(self, server_id: UUID) -> Dict[str, Any]:
        """Get active blocking chains as a tree structure."""
        self._validate_server(server_id)

        # Get the latest collected_at
        latest_time = self.session.query(
            func.max(RunningQuerySnapshot.collected_at)
        ).filter(
            RunningQuerySnapshot.server_id == server_id
        ).scalar()

        if not latest_time:
            return {'chains': [], 'total_blocked_sessions': 0, 'collected_at': None}

        # Get all queries from the latest snapshot
        queries = self.session.query(RunningQuerySnapshot).filter(
            RunningQuerySnapshot.server_id == server_id,
            RunningQuerySnapshot.collected_at == latest_time
        ).all()

        # Build blocking chains
        chains = self._build_blocking_chains(queries)
        total_blocked = sum(self._count_blocked(chain) for chain in chains)

        return {
            'chains': chains,
            'total_blocked_sessions': total_blocked,
            'collected_at': latest_time.isoformat() if latest_time else None
        }

    def _build_blocking_chains(self, queries: List[RunningQuerySnapshot]) -> List[Dict]:
        """Build hierarchical blocking chain tree from query snapshots."""
        # Create lookup by session_id
        by_session = {q.session_id: q for q in queries}

        # Find sessions that are blocking others
        blocked_by_ids = {q.blocking_session_id for q in queries if q.blocking_session_id}

        # Find root blockers (blocking others but not blocked themselves)
        root_blockers = []
        for q in queries:
            if q.session_id in blocked_by_ids and not q.blocking_session_id:
                root_blockers.append(q)

        def build_tree(session_id: int, visited: set) -> Optional[Dict]:
            if session_id in visited:
                return None  # Prevent cycles
            visited.add(session_id)

            query = by_session.get(session_id)
            if not query:
                return None

            # Find all sessions blocked by this one
            blocked = [q for q in queries if q.blocking_session_id == session_id]

            return {
                'session_id': query.session_id,
                'login_name': query.login_name,
                'host_name': query.host_name,
                'program_name': query.program_name,
                'database_name': query.database_name,
                'query_text': query.query_text[:200] if query.query_text else None,
                'duration_ms': query.duration_ms,
                'cpu_time_ms': query.cpu_time_ms,
                'wait_type': query.wait_type,
                'blocked': [build_tree(b.session_id, visited.copy()) for b in blocked]
            }

        return [build_tree(r.session_id, set()) for r in root_blockers if r]

    def _count_blocked(self, node: Dict) -> int:
        """Count total blocked sessions in a chain."""
        if not node:
            return 0
        blocked = node.get('blocked', [])
        return len(blocked) + sum(self._count_blocked(b) for b in blocked if b)

    def get_top_queries(
        self,
        server_id: UUID,
        start: Optional[str],
        end: Optional[str],
        metric: str = 'duration',
        limit: int = 10
    ) -> Dict[str, Any]:
        """Get top N queries by specified metric."""
        self._validate_server(server_id)
        start_dt, end_dt = self._parse_date_range(start, end)

        # Determine the aggregation column and unit
        metric_config = {
            'duration': {'column': RunningQuerySnapshot.duration_ms, 'unit': 'ms', 'agg': func.max},
            'cpu': {'column': RunningQuerySnapshot.cpu_time_ms, 'unit': 'ms', 'agg': func.sum},
            'io': {'column': RunningQuerySnapshot.logical_reads + RunningQuerySnapshot.physical_reads, 'unit': ' reads', 'agg': func.sum},
            'reads': {'column': RunningQuerySnapshot.logical_reads, 'unit': ' reads', 'agg': func.sum},
            'writes': {'column': RunningQuerySnapshot.writes, 'unit': ' writes', 'agg': func.sum},
        }

        if metric not in metric_config:
            metric = 'duration'

        config = metric_config[metric]

        # Query to get top queries aggregated
        results = self.session.query(
            func.left(RunningQuerySnapshot.query_text, 50).label('label'),
            config['agg'](config['column']).label('value'),
            RunningQuerySnapshot.session_id
        ).filter(
            RunningQuerySnapshot.server_id == server_id,
            RunningQuerySnapshot.collected_at.between(start_dt, end_dt),
            RunningQuerySnapshot.query_text.isnot(None)
        ).group_by(
            RunningQuerySnapshot.query_text,
            RunningQuerySnapshot.session_id
        ).order_by(
            desc('value')
        ).limit(limit).all()

        data = []
        for row in results:
            label = row.label or 'Unknown'
            if len(label) >= 50:
                label = label + '...'
            data.append({
                'label': label,
                'value': int(row.value) if row.value else 0,
                'session_id': row.session_id
            })

        return {
            'metric': metric,
            'data': data,
            'unit': config['unit']
        }

    def get_breakdown(
        self,
        server_id: UUID,
        start: Optional[str],
        end: Optional[str],
        dimension: str
    ) -> Dict[str, Any]:
        """Get query distribution breakdown by dimension."""
        self._validate_server(server_id)
        start_dt, end_dt = self._parse_date_range(start, end)

        # Map dimension to column
        dimension_columns = {
            'database': RunningQuerySnapshot.database_name,
            'login': RunningQuerySnapshot.login_name,
            'host': RunningQuerySnapshot.host_name,
            'application': RunningQuerySnapshot.program_name,
            'wait-type': RunningQuerySnapshot.wait_type,
        }

        if dimension not in dimension_columns:
            dimension = 'database'

        column = dimension_columns[dimension]

        # Query for breakdown
        results = self.session.query(
            func.coalesce(column, 'Unknown').label('label'),
            func.count().label('value')
        ).filter(
            RunningQuerySnapshot.server_id == server_id,
            RunningQuerySnapshot.collected_at.between(start_dt, end_dt)
        ).group_by(
            column
        ).order_by(
            desc('value')
        ).limit(11).all()  # Get 11 to see if we need "Other"

        data = []
        total = 0
        for i, row in enumerate(results):
            if i < 10:
                data.append({
                    'label': row.label or 'Unknown',
                    'value': row.value
                })
            total += row.value

        # If there were more than 10, add "Other"
        if len(results) > 10:
            other_value = total - sum(d['value'] for d in data)
            if other_value > 0:
                data.append({
                    'label': 'Other',
                    'value': other_value
                })

        return {
            'dimension': dimension,
            'data': data,
            'total': total
        }

    def get_timeseries(
        self,
        server_id: UUID,
        start: Optional[str],
        end: Optional[str],
        metric: str = 'query-count'
    ) -> Dict[str, Any]:
        """Get time-bucketed metrics for line charts."""
        self._validate_server(server_id)
        start_dt, end_dt = self._parse_date_range(start, end)

        # Determine bucket size based on range
        range_hours = (end_dt - start_dt).total_seconds() / 3600
        if range_hours <= 2:
            interval = 'minute'
            interval_str = '1m'
        elif range_hours <= 24:
            interval = '5 minutes'
            interval_str = '5m'
        elif range_hours <= 168:  # 7 days
            interval = 'hour'
            interval_str = '1h'
        else:
            interval = '6 hours'
            interval_str = '6h'

        # Build the time bucket query based on metric
        if metric == 'query-count':
            agg_func = func.count(RunningQuerySnapshot.id)
            unit = 'queries'
        elif metric == 'avg-duration':
            agg_func = func.avg(RunningQuerySnapshot.duration_ms)
            unit = 'ms'
        elif metric == 'total-cpu':
            agg_func = func.sum(RunningQuerySnapshot.cpu_time_ms)
            unit = 'ms'
        else:
            agg_func = func.count(RunningQuerySnapshot.id)
            unit = 'queries'

        # Use date_trunc for PostgreSQL
        results = self.session.query(
            func.date_trunc(interval.split()[0] if ' ' in interval else interval,
                          RunningQuerySnapshot.collected_at).label('time'),
            agg_func.label('value')
        ).filter(
            RunningQuerySnapshot.server_id == server_id,
            RunningQuerySnapshot.collected_at.between(start_dt, end_dt)
        ).group_by(
            'time'
        ).order_by(
            'time'
        ).all()

        data = []
        for row in results:
            data.append({
                'time': row.time.isoformat() if row.time else None,
                'value': float(row.value) if row.value else 0
            })

        return {
            'metric': metric,
            'interval': interval_str,
            'data': data,
            'unit': unit
        }
