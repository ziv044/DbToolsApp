"""Alert evaluation engine for processing metrics and triggering alerts."""
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models.tenant import (
    AlertRule, Alert, Server, ServerSnapshot, Metric, ActivityLog
)


class AlertEvaluator:
    """Evaluates metrics against alert rules and manages alert lifecycle."""

    # Number of consecutive normal checks required to auto-resolve
    RESOLVE_THRESHOLD = 2

    def __init__(self, session: Session):
        self.session = session
        self._resolved_count: dict[str, int] = {}  # Track consecutive normal readings

    def evaluate_server(
        self,
        server_id: str,
        metrics: dict[str, float],
    ) -> dict:
        """Evaluate all alert rules against a server's metrics.

        Args:
            server_id: The server ID to evaluate
            metrics: Dict of metric_type -> current_value

        Returns:
            Dict with 'new_alerts', 'resolved_alerts', 'active_count'
        """
        new_alerts = []
        resolved_alerts = []

        # Get all enabled rules
        enabled_rules = (
            self.session.query(AlertRule)
            .filter(AlertRule.is_enabled == True)
            .all()
        )

        for rule in enabled_rules:
            metric_value = metrics.get(rule.metric_type)

            if metric_value is None:
                continue

            # Check if rule triggers
            if rule.evaluate(metric_value):
                # Condition is met - check for existing alert
                existing = self._get_active_alert(str(rule.id), server_id)

                if not existing:
                    # Create new alert
                    alert = Alert(
                        rule_id=rule.id,
                        server_id=server_id,
                        metric_value=metric_value,
                        status=Alert.STATUS_ACTIVE,
                    )
                    self.session.add(alert)
                    new_alerts.append(alert)

                    # Log activity
                    self._log_activity(
                        action=ActivityLog.ACTION_ALERT_TRIGGERED,
                        entity_type=ActivityLog.ENTITY_ALERT,
                        entity_id=alert.id,
                        details={
                            'rule_name': rule.name,
                            'metric_type': rule.metric_type,
                            'metric_value': metric_value,
                            'threshold': float(rule.threshold),
                            'severity': rule.severity,
                            'server_id': server_id,
                        }
                    )

                # Reset resolve counter
                self._reset_resolve_counter(str(rule.id), server_id)
            else:
                # Condition is not met - maybe resolve
                existing = self._get_active_alert(str(rule.id), server_id)

                if existing:
                    # Track consecutive normal readings
                    key = f"{rule.id}:{server_id}"
                    self._resolved_count[key] = self._resolved_count.get(key, 0) + 1

                    if self._resolved_count[key] >= self.RESOLVE_THRESHOLD:
                        # Auto-resolve after consecutive normal checks
                        existing.status = Alert.STATUS_RESOLVED
                        existing.resolved_at = datetime.now(timezone.utc)
                        existing.notes = f'Auto-resolved: {rule.metric_type} returned to normal ({metric_value})'
                        resolved_alerts.append(existing)
                        self._reset_resolve_counter(str(rule.id), server_id)

                        # Log activity
                        self._log_activity(
                            action=ActivityLog.ACTION_ALERT_RESOLVED,
                            entity_type=ActivityLog.ENTITY_ALERT,
                            entity_id=existing.id,
                            details={
                                'rule_name': rule.name,
                                'metric_type': rule.metric_type,
                                'metric_value': metric_value,
                                'threshold': float(rule.threshold),
                                'server_id': server_id,
                                'auto_resolved': True,
                            }
                        )

        if new_alerts or resolved_alerts:
            self.session.commit()

        # Update server health status
        self._update_server_health(server_id)

        # Get active alert count
        active_count = (
            self.session.query(Alert)
            .filter(
                Alert.server_id == server_id,
                Alert.status != Alert.STATUS_RESOLVED,
            )
            .count()
        )

        return {
            'new_alerts': [a.to_dict() for a in new_alerts],
            'resolved_alerts': [a.to_dict() for a in resolved_alerts],
            'active_count': active_count,
        }

    def evaluate_all_servers(self) -> dict:
        """Evaluate alerts for all servers with recent snapshots.

        Returns:
            Dict with 'servers_evaluated', 'new_alerts', 'resolved_alerts'
        """
        total_new = 0
        total_resolved = 0
        servers_evaluated = 0

        # Get all servers
        servers = (
            self.session.query(Server)
            .filter(Server.is_deleted == False)
            .all()
        )

        for server in servers:
            # Get latest snapshot
            snapshot = (
                self.session.query(ServerSnapshot)
                .filter(ServerSnapshot.server_id == server.id)
                .order_by(ServerSnapshot.collected_at.desc())
                .first()
            )

            if not snapshot:
                continue

            # Build metrics dict from snapshot
            metrics = self._snapshot_to_metrics(snapshot)

            # Evaluate
            result = self.evaluate_server(str(server.id), metrics)
            total_new += len(result['new_alerts'])
            total_resolved += len(result['resolved_alerts'])
            servers_evaluated += 1

        return {
            'servers_evaluated': servers_evaluated,
            'new_alerts': total_new,
            'resolved_alerts': total_resolved,
        }

    def evaluate_with_aggregates(
        self,
        server_id: str,
        window_minutes: int = 5,
    ) -> dict:
        """Evaluate alerts using aggregated metrics over a time window.

        Args:
            server_id: The server ID to evaluate
            window_minutes: Time window for averaging (default 5 minutes)

        Returns:
            Dict with evaluation results
        """
        # Get snapshots in the time window
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)

        snapshots = (
            self.session.query(ServerSnapshot)
            .filter(
                ServerSnapshot.server_id == server_id,
                ServerSnapshot.collected_at >= cutoff,
            )
            .all()
        )

        if not snapshots:
            return {
                'new_alerts': [],
                'resolved_alerts': [],
                'active_count': 0,
                'error': 'No snapshots in time window',
            }

        # Calculate averages
        metrics = self._calculate_averages(snapshots)

        return self.evaluate_server(server_id, metrics)

    def get_server_health_status(self, server_id: str) -> str:
        """Determine server health status based on active alerts.

        Returns:
            'healthy', 'warning', or 'critical'
        """
        # Check for critical alerts
        critical_count = (
            self.session.query(Alert)
            .join(AlertRule)
            .filter(
                Alert.server_id == server_id,
                Alert.status != Alert.STATUS_RESOLVED,
                AlertRule.severity == AlertRule.SEVERITY_CRITICAL,
            )
            .count()
        )

        if critical_count > 0:
            return 'critical'

        # Check for warning alerts
        warning_count = (
            self.session.query(Alert)
            .join(AlertRule)
            .filter(
                Alert.server_id == server_id,
                Alert.status != Alert.STATUS_RESOLVED,
                AlertRule.severity == AlertRule.SEVERITY_WARNING,
            )
            .count()
        )

        if warning_count > 0:
            return 'warning'

        return 'healthy'

    def _get_active_alert(self, rule_id: str, server_id: str) -> Optional[Alert]:
        """Get an active (non-resolved) alert for a rule and server."""
        return (
            self.session.query(Alert)
            .filter(
                Alert.rule_id == rule_id,
                Alert.server_id == server_id,
                Alert.status != Alert.STATUS_RESOLVED,
            )
            .first()
        )

    def _reset_resolve_counter(self, rule_id: str, server_id: str) -> None:
        """Reset the consecutive normal readings counter."""
        key = f"{rule_id}:{server_id}"
        if key in self._resolved_count:
            del self._resolved_count[key]

    def _update_server_health(self, server_id: str) -> None:
        """Update server's status based on alert health."""
        server = self.session.query(Server).filter(Server.id == server_id).first()
        if not server:
            return

        health = self.get_server_health_status(server_id)

        # Only update if server is online (don't override offline/error status)
        if server.status == Server.STATUS_ONLINE:
            # Optionally update to reflect health
            # For now, keep the status as-is but health is tracked via alerts
            pass

    def _log_activity(
        self,
        action: str,
        entity_type: str,
        entity_id,
        details: dict | None = None,
    ) -> None:
        """Log an activity entry for alert state changes."""
        activity = ActivityLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
        )
        self.session.add(activity)

    def _snapshot_to_metrics(self, snapshot: ServerSnapshot) -> dict[str, float]:
        """Convert a server snapshot to a metrics dictionary."""
        metrics = {}

        if snapshot.cpu_percent is not None:
            metrics['cpu_percent'] = float(snapshot.cpu_percent)
        if snapshot.memory_percent is not None:
            metrics['memory_percent'] = float(snapshot.memory_percent)
        if snapshot.connection_count is not None:
            metrics['connection_count'] = float(snapshot.connection_count)
        if snapshot.batch_requests_sec is not None:
            metrics['batch_requests_sec'] = float(snapshot.batch_requests_sec)
        if snapshot.page_life_expectancy is not None:
            metrics['page_life_expectancy'] = float(snapshot.page_life_expectancy)
        if snapshot.blocked_processes is not None:
            metrics['blocked_processes'] = float(snapshot.blocked_processes)

        return metrics

    def _calculate_averages(self, snapshots: list[ServerSnapshot]) -> dict[str, float]:
        """Calculate average metrics from multiple snapshots."""
        if not snapshots:
            return {}

        metrics = {}
        counts = {}

        for snapshot in snapshots:
            snapshot_metrics = self._snapshot_to_metrics(snapshot)
            for key, value in snapshot_metrics.items():
                if value is not None:
                    metrics[key] = metrics.get(key, 0) + value
                    counts[key] = counts.get(key, 0) + 1

        # Calculate averages
        return {
            key: metrics[key] / counts[key]
            for key in metrics
            if counts.get(key, 0) > 0
        }


def run_alert_evaluation(session: Session) -> dict:
    """Run alert evaluation for all servers.

    This function is designed to be called from the scheduler.

    Args:
        session: Database session

    Returns:
        Dict with evaluation summary
    """
    evaluator = AlertEvaluator(session)
    return evaluator.evaluate_all_servers()
