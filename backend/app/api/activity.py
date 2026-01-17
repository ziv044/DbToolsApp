"""API routes for activity log."""
from datetime import datetime
from flask import request, jsonify, g, Response
import csv
import io

from app.api import api
from app.middleware import require_tenant
from app.services.activity_service import ActivityService


def get_activity_service() -> ActivityService:
    """Get activity service with current tenant session."""
    return ActivityService(g.tenant_session)


@api.route('/activity', methods=['GET'])
@require_tenant
def list_activity():
    """Get activity log entries with optional filters."""
    action = request.args.get('action')
    entity_type = request.args.get('entity_type')
    entity_id = request.args.get('entity_id')
    search = request.args.get('search')
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)

    # Parse dates
    start_date = None
    end_date = None
    if start := request.args.get('start_date'):
        try:
            start_date = datetime.fromisoformat(start.replace('Z', '+00:00'))
        except ValueError:
            pass
    if end := request.args.get('end_date'):
        try:
            end_date = datetime.fromisoformat(end.replace('Z', '+00:00'))
        except ValueError:
            pass

    # Limit max results
    limit = min(limit, 100)

    service = get_activity_service()
    entries, total = service.get_activities(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        search=search,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )

    return jsonify({
        'activities': [e.to_dict() for e in entries],
        'total': total,
        'limit': limit,
        'offset': offset,
    })


@api.route('/activity/<activity_id>', methods=['GET'])
@require_tenant
def get_activity(activity_id: str):
    """Get a single activity entry by ID."""
    service = get_activity_service()
    entry = service.get_activity(activity_id)

    if not entry:
        return jsonify({'error': 'Activity entry not found'}), 404

    return jsonify(entry.to_dict())


@api.route('/activity/filters', methods=['GET'])
@require_tenant
def get_activity_filters():
    """Get available filter options for activity log."""
    service = get_activity_service()

    return jsonify({
        'action_types': service.get_action_types(),
        'entity_types': service.get_entity_types(),
    })


@api.route('/activity/export', methods=['GET'])
@require_tenant
def export_activity_csv():
    """Export activity log to CSV."""
    action = request.args.get('action')
    entity_type = request.args.get('entity_type')
    entity_id = request.args.get('entity_id')
    search = request.args.get('search')

    # Parse dates
    start_date = None
    end_date = None
    if start := request.args.get('start_date'):
        try:
            start_date = datetime.fromisoformat(start.replace('Z', '+00:00'))
        except ValueError:
            pass
    if end := request.args.get('end_date'):
        try:
            end_date = datetime.fromisoformat(end.replace('Z', '+00:00'))
        except ValueError:
            pass

    service = get_activity_service()
    entries, _ = service.get_activities(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        search=search,
        start_date=start_date,
        end_date=end_date,
        limit=10000,  # Max export
        offset=0,
    )

    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(['Timestamp', 'Action', 'Entity Type', 'Entity ID', 'Details'])

    # Data rows
    for entry in entries:
        writer.writerow([
            entry.created_at.isoformat() if entry.created_at else '',
            entry.action,
            entry.entity_type or '',
            str(entry.entity_id) if entry.entity_id else '',
            str(entry.details) if entry.details else '',
        ])

    # Create response
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': 'attachment; filename=activity_log.csv',
            'Content-Type': 'text/csv',
        },
    )


@api.route('/activity/entity/<entity_type>/<entity_id>', methods=['GET'])
@require_tenant
def get_entity_activity(entity_type: str, entity_id: str):
    """Get activity log for a specific entity."""
    limit = request.args.get('limit', 20, type=int)
    limit = min(limit, 100)

    service = get_activity_service()
    entries = service.get_entity_activities(entity_type, entity_id, limit)

    return jsonify({
        'activities': [e.to_dict() for e in entries],
        'entity_type': entity_type,
        'entity_id': entity_id,
    })
