"""Alert rules and alerts service."""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from ..models.tenant import AlertRule, Alert, Server


class AlertValidationError(Exception):
    """Raised when alert rule validation fails."""
    pass


class AlertService:
    """Service for managing alert rules and alerts."""

    def __init__(self, session: Session):
        self.session = session

    # ==================== Alert Rules ====================

    def validate_rule_input(
        self,
        name: str,
        metric_type: str,
        operator: str,
        threshold: float,
        severity: str,
    ) -> None:
        """Validate alert rule input data."""
        errors = []

        if not name or not name.strip():
            errors.append('Name is required')

        if metric_type not in AlertRule.VALID_METRIC_TYPES:
            errors.append(f'Invalid metric type. Valid types: {", ".join(AlertRule.VALID_METRIC_TYPES)}')

        if operator not in AlertRule.VALID_OPERATORS:
            errors.append(f'Invalid operator. Valid operators: {", ".join(AlertRule.VALID_OPERATORS)}')

        if severity not in AlertRule.VALID_SEVERITIES:
            errors.append(f'Invalid severity. Valid severities: {", ".join(AlertRule.VALID_SEVERITIES)}')

        if errors:
            raise AlertValidationError(errors)

    def create_rule(
        self,
        name: str,
        metric_type: str,
        operator: str,
        threshold: float,
        severity: str,
        is_enabled: bool = True,
    ) -> AlertRule:
        """Create a new alert rule."""
        self.validate_rule_input(name, metric_type, operator, threshold, severity)

        rule = AlertRule(
            name=name.strip(),
            metric_type=metric_type,
            operator=operator,
            threshold=threshold,
            severity=severity,
            is_enabled=is_enabled,
        )

        self.session.add(rule)
        self.session.commit()
        self.session.refresh(rule)

        return rule

    def get_rule(self, rule_id: str) -> Optional[AlertRule]:
        """Get an alert rule by ID."""
        return self.session.query(AlertRule).filter(AlertRule.id == rule_id).first()

    def get_all_rules(
        self,
        metric_type: Optional[str] = None,
        severity: Optional[str] = None,
        enabled: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[AlertRule], int]:
        """Get all alert rules with optional filters."""
        query = self.session.query(AlertRule)

        if metric_type:
            query = query.filter(AlertRule.metric_type == metric_type)
        if severity:
            query = query.filter(AlertRule.severity == severity)
        if enabled is not None:
            query = query.filter(AlertRule.is_enabled == enabled)

        total = query.count()
        rules = query.order_by(AlertRule.created_at.desc()).offset(offset).limit(limit).all()

        return rules, total

    def update_rule(
        self,
        rule_id: str,
        name: Optional[str] = None,
        metric_type: Optional[str] = None,
        operator: Optional[str] = None,
        threshold: Optional[float] = None,
        severity: Optional[str] = None,
        is_enabled: Optional[bool] = None,
    ) -> Optional[AlertRule]:
        """Update an alert rule."""
        rule = self.get_rule(rule_id)
        if not rule:
            return None

        # Validate any provided fields
        final_name = name if name is not None else rule.name
        final_metric_type = metric_type if metric_type is not None else rule.metric_type
        final_operator = operator if operator is not None else rule.operator
        final_threshold = threshold if threshold is not None else float(rule.threshold)
        final_severity = severity if severity is not None else rule.severity

        self.validate_rule_input(
            final_name, final_metric_type, final_operator, final_threshold, final_severity
        )

        if name is not None:
            rule.name = name.strip()
        if metric_type is not None:
            rule.metric_type = metric_type
        if operator is not None:
            rule.operator = operator
        if threshold is not None:
            rule.threshold = threshold
        if severity is not None:
            rule.severity = severity
        if is_enabled is not None:
            rule.is_enabled = is_enabled

        self.session.commit()
        self.session.refresh(rule)

        return rule

    def delete_rule(self, rule_id: str) -> bool:
        """Delete an alert rule."""
        rule = self.get_rule(rule_id)
        if not rule:
            return False

        self.session.delete(rule)
        self.session.commit()

        return True

    def enable_rule(self, rule_id: str) -> Optional[AlertRule]:
        """Enable an alert rule."""
        return self.update_rule(rule_id, is_enabled=True)

    def disable_rule(self, rule_id: str) -> Optional[AlertRule]:
        """Disable an alert rule."""
        return self.update_rule(rule_id, is_enabled=False)

    # ==================== Alerts ====================

    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Get an alert by ID."""
        return self.session.query(Alert).filter(Alert.id == alert_id).first()

    def get_all_alerts(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        server_id: Optional[str] = None,
        rule_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[Alert], int]:
        """Get all alerts with optional filters."""
        query = self.session.query(Alert).join(AlertRule)

        if status:
            query = query.filter(Alert.status == status)
        if severity:
            query = query.filter(AlertRule.severity == severity)
        if server_id:
            query = query.filter(Alert.server_id == server_id)
        if rule_id:
            query = query.filter(Alert.rule_id == rule_id)

        total = query.count()
        alerts = query.order_by(Alert.triggered_at.desc()).offset(offset).limit(limit).all()

        return alerts, total

    def get_active_alerts(
        self,
        server_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[Alert], int]:
        """Get active (non-resolved) alerts."""
        return self.get_all_alerts(
            status=None,  # We'll filter for non-resolved
            server_id=server_id,
            limit=limit,
            offset=offset,
        )

    def acknowledge_alert(
        self,
        alert_id: str,
        acknowledged_by: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Optional[Alert]:
        """Acknowledge an active alert."""
        alert = self.get_alert(alert_id)
        if not alert:
            return None

        if alert.status == Alert.STATUS_RESOLVED:
            return alert  # Already resolved, nothing to do

        alert.status = Alert.STATUS_ACKNOWLEDGED
        alert.acknowledged_at = datetime.now(timezone.utc)
        alert.acknowledged_by = acknowledged_by
        if notes:
            alert.notes = notes

        self.session.commit()
        self.session.refresh(alert)

        return alert

    def resolve_alert(self, alert_id: str, notes: Optional[str] = None) -> Optional[Alert]:
        """Resolve an alert."""
        alert = self.get_alert(alert_id)
        if not alert:
            return None

        alert.status = Alert.STATUS_RESOLVED
        alert.resolved_at = datetime.now(timezone.utc)
        if notes:
            alert.notes = notes

        self.session.commit()
        self.session.refresh(alert)

        return alert

    def create_alert(
        self,
        rule_id: str,
        server_id: str,
        metric_value: Optional[float] = None,
    ) -> Alert:
        """Create a new alert for a rule and server."""
        alert = Alert(
            rule_id=rule_id,
            server_id=server_id,
            metric_value=metric_value,
            status=Alert.STATUS_ACTIVE,
        )

        self.session.add(alert)
        self.session.commit()
        self.session.refresh(alert)

        return alert

    def get_active_alert_for_rule_server(
        self,
        rule_id: str,
        server_id: str,
    ) -> Optional[Alert]:
        """Get an active alert for a specific rule and server combination."""
        return (
            self.session.query(Alert)
            .filter(
                Alert.rule_id == rule_id,
                Alert.server_id == server_id,
                Alert.status != Alert.STATUS_RESOLVED,
            )
            .first()
        )

    def auto_resolve_alerts_for_server(
        self,
        server_id: str,
        metrics: dict[str, float],
    ) -> list[Alert]:
        """Auto-resolve alerts where the condition is no longer met.

        Args:
            server_id: The server ID to check alerts for
            metrics: Dict of metric_type -> current_value

        Returns:
            List of alerts that were auto-resolved
        """
        resolved_alerts = []

        # Get all active alerts for this server
        active_alerts = (
            self.session.query(Alert)
            .join(AlertRule)
            .filter(
                Alert.server_id == server_id,
                Alert.status != Alert.STATUS_RESOLVED,
                AlertRule.is_enabled == True,
            )
            .all()
        )

        for alert in active_alerts:
            rule = alert.rule
            metric_value = metrics.get(rule.metric_type)

            if metric_value is not None:
                # Check if condition is still met
                if not rule.evaluate(metric_value):
                    # Condition no longer met, auto-resolve
                    alert.status = Alert.STATUS_RESOLVED
                    alert.resolved_at = datetime.now(timezone.utc)
                    alert.notes = f'Auto-resolved: {rule.metric_type} is now {metric_value}'
                    resolved_alerts.append(alert)

        if resolved_alerts:
            self.session.commit()

        return resolved_alerts

    def evaluate_rules_for_server(
        self,
        server_id: str,
        metrics: dict[str, float],
    ) -> list[Alert]:
        """Evaluate all enabled rules against server metrics and create alerts.

        Args:
            server_id: The server ID to evaluate
            metrics: Dict of metric_type -> current_value

        Returns:
            List of new alerts created
        """
        new_alerts = []

        # Get all enabled rules
        enabled_rules = (
            self.session.query(AlertRule)
            .filter(AlertRule.is_enabled == True)
            .all()
        )

        for rule in enabled_rules:
            metric_value = metrics.get(rule.metric_type)

            if metric_value is not None:
                # Check if rule triggers
                if rule.evaluate(metric_value):
                    # Check if there's already an active alert
                    existing_alert = self.get_active_alert_for_rule_server(
                        str(rule.id), server_id
                    )

                    if not existing_alert:
                        # Create new alert
                        alert = self.create_alert(
                            rule_id=str(rule.id),
                            server_id=server_id,
                            metric_value=metric_value,
                        )
                        new_alerts.append(alert)

        return new_alerts

    def get_alert_counts_by_severity(self) -> dict[str, int]:
        """Get count of active alerts grouped by severity."""
        from sqlalchemy import func

        results = (
            self.session.query(AlertRule.severity, func.count(Alert.id))
            .join(Alert, Alert.rule_id == AlertRule.id)
            .filter(Alert.status != Alert.STATUS_RESOLVED)
            .group_by(AlertRule.severity)
            .all()
        )

        counts = {s: 0 for s in AlertRule.VALID_SEVERITIES}
        for severity, count in results:
            counts[severity] = count

        return counts
