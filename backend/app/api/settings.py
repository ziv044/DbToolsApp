"""Settings API endpoints."""
from flask import request, g

from app.api import api
from app.services.retention_service import RetentionService, RetentionValidationError


@api.route('/settings/retention', methods=['GET'])
def get_retention_settings():
    """
    Get current retention settings.

    Returns:
        200: Retention configuration
    """
    service = RetentionService(g.tenant_session)
    config = service.get_retention_config()

    return {'retention': config}, 200


@api.route('/settings/retention', methods=['PUT'])
def update_retention_settings():
    """
    Update retention settings.

    Body:
        retention_days: Number of days to retain metrics (1-365)

    Returns:
        200: Updated retention configuration
        400: Validation error
    """
    data = request.get_json()

    if not data:
        return {'error': 'Request body is required'}, 400

    retention_days = data.get('retention_days')

    if retention_days is None:
        return {'error': 'retention_days is required'}, 400

    if not isinstance(retention_days, int):
        return {'error': 'retention_days must be an integer'}, 400

    service = RetentionService(g.tenant_session)

    try:
        service.set_retention_days(retention_days)
        config = service.get_retention_config()
        return {'retention': config}, 200
    except RetentionValidationError as e:
        return {'error': e.message, 'field': e.field}, 400


@api.route('/metrics/stats', methods=['GET'])
def get_metrics_stats():
    """
    Get storage statistics for metrics.

    Returns:
        200: Metrics storage statistics
    """
    service = RetentionService(g.tenant_session)
    stats = service.get_metrics_stats()

    return {'stats': stats}, 200
