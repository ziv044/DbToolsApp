"""Analytics API endpoints for query dashboard."""
from flask import request, jsonify, g
from uuid import UUID

from app.api import api
from app.middleware import require_tenant
from app.services.analytics_service import AnalyticsService, AnalyticsServiceError


@api.route('/analytics/queries/running', methods=['GET'])
@require_tenant
def get_running_queries_analytics():
    """
    Get currently running queries for a server (latest snapshot).

    Query params:
        server_id: UUID of the server (required)

    Returns:
        200: Table data with columns and rows
        400: Invalid server_id
        404: Server not found
    """
    server_id = request.args.get('server_id')
    if not server_id:
        return jsonify({
            'error': {
                'code': 'MISSING_PARAMETER',
                'message': 'server_id is required'
            }
        }), 400

    try:
        uuid_id = UUID(server_id)
    except ValueError:
        return jsonify({
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid server_id format'
            }
        }), 400

    try:
        service = AnalyticsService(g.tenant_session)
        data = service.get_running_queries(uuid_id)
        return jsonify(data), 200
    except AnalyticsServiceError as e:
        status = 404 if e.code == 'NOT_FOUND' else 400
        return jsonify({'error': {'code': e.code, 'message': e.message}}), status


@api.route('/analytics/queries/blocking-chains', methods=['GET'])
@require_tenant
def get_blocking_chains():
    """
    Get active blocking chains as a tree structure.

    Query params:
        server_id: UUID of the server (required)

    Returns:
        200: Blocking chain tree data
        400: Invalid server_id
        404: Server not found
    """
    server_id = request.args.get('server_id')
    if not server_id:
        return jsonify({
            'error': {
                'code': 'MISSING_PARAMETER',
                'message': 'server_id is required'
            }
        }), 400

    try:
        uuid_id = UUID(server_id)
    except ValueError:
        return jsonify({
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid server_id format'
            }
        }), 400

    try:
        service = AnalyticsService(g.tenant_session)
        data = service.get_blocking_chains(uuid_id)
        return jsonify(data), 200
    except AnalyticsServiceError as e:
        status = 404 if e.code == 'NOT_FOUND' else 400
        return jsonify({'error': {'code': e.code, 'message': e.message}}), status


@api.route('/analytics/queries/top', methods=['GET'])
@require_tenant
def get_top_queries():
    """
    Get top N queries by specified metric.

    Query params:
        server_id: UUID of the server (required)
        start: Start datetime ISO format (optional, default: 1 hour ago)
        end: End datetime ISO format (optional, default: now)
        metric: duration | cpu | io | reads | writes (default: duration)
        limit: Number of results (default: 10, max: 100)

    Returns:
        200: Bar chart data with label, value pairs
        400: Invalid parameters
        404: Server not found
    """
    server_id = request.args.get('server_id')
    if not server_id:
        return jsonify({
            'error': {
                'code': 'MISSING_PARAMETER',
                'message': 'server_id is required'
            }
        }), 400

    try:
        uuid_id = UUID(server_id)
    except ValueError:
        return jsonify({
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid server_id format'
            }
        }), 400

    start = request.args.get('start')
    end = request.args.get('end')
    metric = request.args.get('metric', 'duration')
    limit = request.args.get('limit', 10, type=int)

    # Validate metric
    valid_metrics = ['duration', 'cpu', 'io', 'reads', 'writes']
    if metric not in valid_metrics:
        return jsonify({
            'error': {
                'code': 'INVALID_METRIC',
                'message': f'Invalid metric. Must be one of: {", ".join(valid_metrics)}'
            }
        }), 400

    # Validate limit
    if limit < 1 or limit > 100:
        return jsonify({
            'error': {
                'code': 'INVALID_LIMIT',
                'message': 'Limit must be between 1 and 100'
            }
        }), 400

    try:
        service = AnalyticsService(g.tenant_session)
        data = service.get_top_queries(uuid_id, start, end, metric, limit)
        return jsonify(data), 200
    except AnalyticsServiceError as e:
        status = 404 if e.code == 'NOT_FOUND' else 400
        return jsonify({'error': {'code': e.code, 'message': e.message}}), status


@api.route('/analytics/breakdowns/by-database', methods=['GET'])
@require_tenant
def get_breakdown_by_database():
    """Get query distribution by database."""
    return _get_breakdown('database')


@api.route('/analytics/breakdowns/by-login', methods=['GET'])
@require_tenant
def get_breakdown_by_login():
    """Get query distribution by login."""
    return _get_breakdown('login')


@api.route('/analytics/breakdowns/by-host', methods=['GET'])
@require_tenant
def get_breakdown_by_host():
    """Get query distribution by host."""
    return _get_breakdown('host')


@api.route('/analytics/breakdowns/by-application', methods=['GET'])
@require_tenant
def get_breakdown_by_application():
    """Get query distribution by application (program_name)."""
    return _get_breakdown('application')


@api.route('/analytics/breakdowns/by-wait-type', methods=['GET'])
@require_tenant
def get_breakdown_by_wait_type():
    """Get query distribution by wait type."""
    return _get_breakdown('wait-type')


def _get_breakdown(dimension: str):
    """
    Common handler for breakdown endpoints.

    Query params:
        server_id: UUID of the server (required)
        start: Start datetime ISO format (optional)
        end: End datetime ISO format (optional)

    Returns:
        200: Pie chart data with label, value pairs
        400: Invalid parameters
        404: Server not found
    """
    server_id = request.args.get('server_id')
    if not server_id:
        return jsonify({
            'error': {
                'code': 'MISSING_PARAMETER',
                'message': 'server_id is required'
            }
        }), 400

    try:
        uuid_id = UUID(server_id)
    except ValueError:
        return jsonify({
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid server_id format'
            }
        }), 400

    start = request.args.get('start')
    end = request.args.get('end')

    try:
        service = AnalyticsService(g.tenant_session)
        data = service.get_breakdown(uuid_id, start, end, dimension)
        return jsonify(data), 200
    except AnalyticsServiceError as e:
        status = 404 if e.code == 'NOT_FOUND' else 400
        return jsonify({'error': {'code': e.code, 'message': e.message}}), status


@api.route('/analytics/timeseries/query-count', methods=['GET'])
@require_tenant
def get_timeseries_query_count():
    """Get query count over time."""
    return _get_timeseries('query-count')


@api.route('/analytics/timeseries/avg-duration', methods=['GET'])
@require_tenant
def get_timeseries_avg_duration():
    """Get average query duration over time."""
    return _get_timeseries('avg-duration')


@api.route('/analytics/timeseries/total-cpu', methods=['GET'])
@require_tenant
def get_timeseries_total_cpu():
    """Get total CPU time over time."""
    return _get_timeseries('total-cpu')


def _get_timeseries(metric: str):
    """
    Common handler for time series endpoints.

    Query params:
        server_id: UUID of the server (required)
        start: Start datetime ISO format (optional)
        end: End datetime ISO format (optional)

    Returns:
        200: Time series data with time, value pairs
        400: Invalid parameters
        404: Server not found
    """
    server_id = request.args.get('server_id')
    if not server_id:
        return jsonify({
            'error': {
                'code': 'MISSING_PARAMETER',
                'message': 'server_id is required'
            }
        }), 400

    try:
        uuid_id = UUID(server_id)
    except ValueError:
        return jsonify({
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid server_id format'
            }
        }), 400

    start = request.args.get('start')
    end = request.args.get('end')

    try:
        service = AnalyticsService(g.tenant_session)
        data = service.get_timeseries(uuid_id, start, end, metric)
        return jsonify(data), 200
    except AnalyticsServiceError as e:
        status = 404 if e.code == 'NOT_FOUND' else 400
        return jsonify({'error': {'code': e.code, 'message': e.message}}), status
