"""API routes for alert rules and alerts management."""
from flask import request, jsonify, g

from app.api import api
from app.middleware import require_tenant
from app.services.alert_service import AlertService, AlertValidationError
from app.models.tenant import Alert


def get_alert_service() -> AlertService:
    """Get alert service with current tenant session."""
    return AlertService(g.tenant_session)


# ==================== Alert Rules ====================

@api.route('/alert-rules', methods=['POST'])
@require_tenant
def create_alert_rule():
    """Create a new alert rule."""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    required_fields = ['name', 'metric_type', 'operator', 'threshold', 'severity']
    missing = [f for f in required_fields if f not in data]
    if missing:
        return jsonify({'error': f'Missing required fields: {", ".join(missing)}'}), 400

    try:
        service = get_alert_service()
        rule = service.create_rule(
            name=data['name'],
            metric_type=data['metric_type'],
            operator=data['operator'],
            threshold=float(data['threshold']),
            severity=data['severity'],
            is_enabled=data.get('is_enabled', True),
        )
        return jsonify(rule.to_dict()), 201

    except AlertValidationError as e:
        return jsonify({'error': 'Validation failed', 'details': e.args[0]}), 400
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@api.route('/alert-rules', methods=['GET'])
@require_tenant
def list_alert_rules():
    """Get all alert rules with optional filters."""
    metric_type = request.args.get('metric_type')
    severity = request.args.get('severity')
    enabled = request.args.get('enabled')
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)

    enabled_bool = None
    if enabled is not None:
        enabled_bool = enabled.lower() == 'true'

    service = get_alert_service()
    rules, total = service.get_all_rules(
        metric_type=metric_type,
        severity=severity,
        enabled=enabled_bool,
        limit=limit,
        offset=offset,
    )

    return jsonify({
        'rules': [r.to_dict() for r in rules],
        'total': total,
        'limit': limit,
        'offset': offset,
    })


@api.route('/alert-rules/<rule_id>', methods=['GET'])
@require_tenant
def get_alert_rule(rule_id: str):
    """Get an alert rule by ID."""
    service = get_alert_service()
    rule = service.get_rule(rule_id)

    if not rule:
        return jsonify({'error': 'Alert rule not found'}), 404

    return jsonify(rule.to_dict())


@api.route('/alert-rules/<rule_id>', methods=['PUT'])
@require_tenant
def update_alert_rule(rule_id: str):
    """Update an alert rule."""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    try:
        service = get_alert_service()
        rule = service.update_rule(
            rule_id=rule_id,
            name=data.get('name'),
            metric_type=data.get('metric_type'),
            operator=data.get('operator'),
            threshold=float(data['threshold']) if 'threshold' in data else None,
            severity=data.get('severity'),
            is_enabled=data.get('is_enabled'),
        )

        if not rule:
            return jsonify({'error': 'Alert rule not found'}), 404

        return jsonify(rule.to_dict())

    except AlertValidationError as e:
        return jsonify({'error': 'Validation failed', 'details': e.args[0]}), 400
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@api.route('/alert-rules/<rule_id>', methods=['DELETE'])
@require_tenant
def delete_alert_rule(rule_id: str):
    """Delete an alert rule."""
    service = get_alert_service()
    deleted = service.delete_rule(rule_id)

    if not deleted:
        return jsonify({'error': 'Alert rule not found'}), 404

    return '', 204


@api.route('/alert-rules/<rule_id>/enable', methods=['POST'])
@require_tenant
def enable_alert_rule(rule_id: str):
    """Enable an alert rule."""
    service = get_alert_service()
    rule = service.enable_rule(rule_id)

    if not rule:
        return jsonify({'error': 'Alert rule not found'}), 404

    return jsonify(rule.to_dict())


@api.route('/alert-rules/<rule_id>/disable', methods=['POST'])
@require_tenant
def disable_alert_rule(rule_id: str):
    """Disable an alert rule."""
    service = get_alert_service()
    rule = service.disable_rule(rule_id)

    if not rule:
        return jsonify({'error': 'Alert rule not found'}), 404

    return jsonify(rule.to_dict())


# ==================== Alerts ====================

@api.route('/alerts', methods=['GET'])
@require_tenant
def list_alerts():
    """Get all alerts with optional filters."""
    status = request.args.get('status')
    severity = request.args.get('severity')
    server_id = request.args.get('server_id')
    rule_id = request.args.get('rule_id')
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)

    service = get_alert_service()
    alerts, total = service.get_all_alerts(
        status=status,
        severity=severity,
        server_id=server_id,
        rule_id=rule_id,
        limit=limit,
        offset=offset,
    )

    return jsonify({
        'alerts': [a.to_dict(include_rule=True, include_server=True) for a in alerts],
        'total': total,
        'limit': limit,
        'offset': offset,
    })


@api.route('/alerts/active', methods=['GET'])
@require_tenant
def list_active_alerts():
    """Get active (non-resolved) alerts."""
    server_id = request.args.get('server_id')
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)

    service = get_alert_service()

    # Query active and acknowledged alerts
    alerts, total = service.get_all_alerts(
        server_id=server_id,
        limit=limit,
        offset=offset,
    )

    # Filter to only active/acknowledged
    active_alerts = [a for a in alerts if a.status != Alert.STATUS_RESOLVED]

    return jsonify({
        'alerts': [a.to_dict(include_rule=True, include_server=True) for a in active_alerts],
        'total': len(active_alerts),
        'limit': limit,
        'offset': offset,
    })


@api.route('/alerts/counts', methods=['GET'])
@require_tenant
def get_alert_counts():
    """Get count of active alerts by severity."""
    service = get_alert_service()
    counts = service.get_alert_counts_by_severity()

    return jsonify({
        'counts': counts,
        'total': sum(counts.values()),
    })


@api.route('/alerts/<alert_id>', methods=['GET'])
@require_tenant
def get_alert(alert_id: str):
    """Get an alert by ID."""
    service = get_alert_service()
    alert = service.get_alert(alert_id)

    if not alert:
        return jsonify({'error': 'Alert not found'}), 404

    return jsonify(alert.to_dict(include_rule=True, include_server=True))


@api.route('/alerts/<alert_id>/acknowledge', methods=['POST'])
@require_tenant
def acknowledge_alert(alert_id: str):
    """Acknowledge an alert."""
    data = request.get_json() or {}

    service = get_alert_service()
    alert = service.acknowledge_alert(
        alert_id=alert_id,
        acknowledged_by=data.get('acknowledged_by'),
        notes=data.get('notes'),
    )

    if not alert:
        return jsonify({'error': 'Alert not found'}), 404

    return jsonify(alert.to_dict(include_rule=True, include_server=True))


@api.route('/alerts/<alert_id>/resolve', methods=['POST'])
@require_tenant
def resolve_alert(alert_id: str):
    """Resolve an alert."""
    data = request.get_json() or {}

    service = get_alert_service()
    alert = service.resolve_alert(
        alert_id=alert_id,
        notes=data.get('notes'),
    )

    if not alert:
        return jsonify({'error': 'Alert not found'}), 404

    return jsonify(alert.to_dict(include_rule=True, include_server=True))
