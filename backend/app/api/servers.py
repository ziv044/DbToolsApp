"""Server management API endpoints."""
from flask import request, jsonify, g
from uuid import UUID

from app.api import api
from app.middleware import require_tenant
from app.services.server_service import (
    ServerService,
    ServerValidationError,
    ServerNotFoundError,
    CreateServerInput,
    UpdateServerInput
)
from app.connectors.sqlserver import SQLServerConnector, SQLServerConnectionError, PYODBC_AVAILABLE
from app.services.deployment_service import DeploymentService, DeploymentError
from app.services.collection_config_service import (
    CollectionConfigService,
    CollectionConfigError,
    CollectionConfigValidationError,
)
from app.services.health_service import HealthService
from app.services.metrics_service import MetricsService, MetricsServiceError
from app.services.running_queries_service import RunningQueriesService


@api.route('/servers', methods=['GET'])
@require_tenant
def list_servers():
    """List all servers for the current tenant."""
    service = ServerService(g.tenant_session)
    servers = service.get_all()

    return jsonify({
        'servers': [s.to_dict() for s in servers],
        'total': len(servers)
    })


@api.route('/servers/test-connection', methods=['POST'])
@require_tenant
def test_connection():
    """Test SQL Server connectivity without saving."""
    if not PYODBC_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'SQL Server connectivity not available. pyodbc is not installed.',
            'error_code': 'DRIVER_NOT_INSTALLED'
        }), 503

    data = request.get_json() or {}

    # Validate required fields
    hostname = data.get('hostname')
    if not hostname:
        return jsonify({
            'success': False,
            'error': 'Hostname is required',
            'error_code': 'VALIDATION_ERROR'
        }), 400

    auth_type = data.get('auth_type', 'sql')
    if auth_type not in ('sql', 'windows'):
        return jsonify({
            'success': False,
            'error': 'Invalid auth_type. Must be "sql" or "windows"',
            'error_code': 'VALIDATION_ERROR'
        }), 400

    if auth_type == 'sql' and not data.get('username'):
        return jsonify({
            'success': False,
            'error': 'Username is required for SQL authentication',
            'error_code': 'VALIDATION_ERROR'
        }), 400

    try:
        connector = SQLServerConnector()
        result = connector.test_connection(
            hostname=hostname,
            port=data.get('port', 1433),
            instance_name=data.get('instance_name'),
            auth_type=auth_type,
            username=data.get('username'),
            password=data.get('password')
        )

        if result.success:
            return jsonify(result.to_dict()), 200
        else:
            return jsonify(result.to_dict()), 400

    except SQLServerConnectionError as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'error_code': 'CONNECTION_ERROR'
        }), 400


@api.route('/servers', methods=['POST'])
@require_tenant
def create_server():
    """Create a new server."""
    data = request.get_json() or {}
    validate = data.get('validate', False)

    # If validate=true, test connection before creating
    if validate:
        if not PYODBC_AVAILABLE:
            return jsonify({
                'error': {
                    'code': 'DRIVER_NOT_INSTALLED',
                    'message': 'SQL Server connectivity not available. pyodbc is not installed.'
                }
            }), 503

        try:
            connector = SQLServerConnector()
            result = connector.test_connection(
                hostname=data.get('hostname', ''),
                port=data.get('port', 1433),
                instance_name=data.get('instance_name'),
                auth_type=data.get('auth_type', 'sql'),
                username=data.get('username'),
                password=data.get('password')
            )

            if not result.success:
                return jsonify({
                    'error': {
                        'code': result.error_code or 'CONNECTION_FAILED',
                        'message': result.error or 'Connection test failed'
                    }
                }), 400

        except SQLServerConnectionError as e:
            return jsonify({
                'error': {
                    'code': 'CONNECTION_ERROR',
                    'message': str(e)
                }
            }), 400

    try:
        input = CreateServerInput(
            name=data.get('name', ''),
            hostname=data.get('hostname', ''),
            port=data.get('port', 1433),
            instance_name=data.get('instance_name'),
            auth_type=data.get('auth_type', 'sql'),
            username=data.get('username'),
            password=data.get('password'),
        )

        service = ServerService(g.tenant_session)
        server = service.create(input)
        g.tenant_session.commit()

        return jsonify(server.to_dict()), 201

    except ServerValidationError as e:
        g.tenant_session.rollback()
        return jsonify({
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': e.message,
                'field': e.field
            }
        }), 400


@api.route('/servers/<server_id>', methods=['GET'])
@require_tenant
def get_server(server_id: str):
    """Get a server by ID."""
    try:
        uuid_id = UUID(server_id)
    except ValueError:
        return jsonify({
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid server ID format'
            }
        }), 400

    try:
        service = ServerService(g.tenant_session)
        server = service.get_by_id(uuid_id)
        return jsonify(server.to_dict(include_labels=True))

    except ServerNotFoundError:
        return jsonify({
            'error': {
                'code': 'NOT_FOUND',
                'message': f'Server with id {server_id} not found'
            }
        }), 404


@api.route('/servers/<server_id>', methods=['PUT'])
@require_tenant
def update_server(server_id: str):
    """Update a server."""
    try:
        uuid_id = UUID(server_id)
    except ValueError:
        return jsonify({
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid server ID format'
            }
        }), 400

    data = request.get_json() or {}

    try:
        input = UpdateServerInput(
            name=data.get('name'),
            hostname=data.get('hostname'),
            port=data.get('port'),
            instance_name=data.get('instance_name'),
            auth_type=data.get('auth_type'),
            username=data.get('username'),
            password=data.get('password'),
        )

        service = ServerService(g.tenant_session)
        server = service.update(uuid_id, input)
        g.tenant_session.commit()

        return jsonify(server.to_dict())

    except ServerNotFoundError:
        return jsonify({
            'error': {
                'code': 'NOT_FOUND',
                'message': f'Server with id {server_id} not found'
            }
        }), 404
    except ServerValidationError as e:
        g.tenant_session.rollback()
        return jsonify({
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': e.message,
                'field': e.field
            }
        }), 400


@api.route('/servers/<server_id>', methods=['DELETE'])
@require_tenant
def delete_server(server_id: str):
    """Soft delete a server."""
    try:
        uuid_id = UUID(server_id)
    except ValueError:
        return jsonify({
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid server ID format'
            }
        }), 400

    try:
        service = ServerService(g.tenant_session)
        service.delete(uuid_id)
        g.tenant_session.commit()

        return '', 204

    except ServerNotFoundError:
        return jsonify({
            'error': {
                'code': 'NOT_FOUND',
                'message': f'Server with id {server_id} not found'
            }
        }), 404


@api.route('/servers/<server_id>/deploy', methods=['POST'])
@require_tenant
def deploy_monitoring(server_id: str):
    """Deploy monitoring objects to a SQL Server."""
    try:
        uuid_id = UUID(server_id)
    except ValueError:
        return jsonify({
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid server ID format'
            }
        }), 400

    try:
        service = DeploymentService(g.tenant_session)
        result = service.deploy(uuid_id)

        if result.success:
            return jsonify(result.to_dict()), 200
        else:
            return jsonify(result.to_dict()), 400

    except DeploymentError as e:
        return jsonify({
            'error': {
                'code': e.code,
                'message': e.message
            }
        }), 400 if e.code != 'DRIVER_NOT_INSTALLED' else 503


@api.route('/servers/<server_id>/deployment-status', methods=['GET'])
@require_tenant
def get_deployment_status(server_id: str):
    """Get deployment status for a SQL Server."""
    try:
        uuid_id = UUID(server_id)
    except ValueError:
        return jsonify({
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid server ID format'
            }
        }), 400

    try:
        service = DeploymentService(g.tenant_session)
        result = service.get_status(uuid_id)

        return jsonify(result.to_dict()), 200

    except DeploymentError as e:
        return jsonify({
            'error': {
                'code': e.code,
                'message': e.message
            }
        }), 400 if e.code != 'DRIVER_NOT_INSTALLED' else 503


@api.route('/servers/<server_id>/permissions', methods=['GET'])
@require_tenant
def check_permissions(server_id: str):
    """Check deployment permissions for a SQL Server."""
    try:
        uuid_id = UUID(server_id)
    except ValueError:
        return jsonify({
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid server ID format'
            }
        }), 400

    try:
        service = DeploymentService(g.tenant_session)
        result = service.check_permissions(uuid_id)

        return jsonify(result.to_dict()), 200

    except DeploymentError as e:
        return jsonify({
            'error': {
                'code': e.code,
                'message': e.message
            }
        }), 400 if e.code != 'DRIVER_NOT_INSTALLED' else 503


@api.route('/servers/<server_id>/collection-config', methods=['GET'])
@require_tenant
def get_collection_config(server_id: str):
    """Get collection config for a server."""
    try:
        uuid_id = UUID(server_id)
    except ValueError:
        return jsonify({
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid server ID format'
            }
        }), 400

    try:
        service = CollectionConfigService(g.tenant_session)
        config = service.get_config(uuid_id)

        return jsonify(config.to_dict()), 200

    except CollectionConfigError as e:
        return jsonify({
            'error': {
                'code': e.code,
                'message': e.message
            }
        }), 404 if e.code == 'SERVER_NOT_FOUND' else 400


@api.route('/servers/<server_id>/collection-config', methods=['PUT'])
@require_tenant
def update_collection_config(server_id: str):
    """Update collection config for a server."""
    try:
        uuid_id = UUID(server_id)
    except ValueError:
        return jsonify({
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid server ID format'
            }
        }), 400

    data = request.get_json() or {}

    try:
        service = CollectionConfigService(g.tenant_session)
        config = service.update_config(
            server_id=uuid_id,
            interval_seconds=data.get('interval_seconds'),
            enabled=data.get('enabled'),
            metrics_enabled=data.get('metrics_enabled'),
        )

        return jsonify(config.to_dict()), 200

    except CollectionConfigValidationError as e:
        return jsonify({
            'error': {
                'code': e.code,
                'message': e.message,
                'field': e.field
            }
        }), 400
    except CollectionConfigError as e:
        return jsonify({
            'error': {
                'code': e.code,
                'message': e.message
            }
        }), 404 if e.code == 'SERVER_NOT_FOUND' else 400


@api.route('/servers/<server_id>/collection/start', methods=['POST'])
@require_tenant
def start_collection(server_id: str):
    """Start data collection for a server."""
    try:
        uuid_id = UUID(server_id)
    except ValueError:
        return jsonify({
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid server ID format'
            }
        }), 400

    try:
        service = CollectionConfigService(g.tenant_session)
        config = service.start_collection(uuid_id)

        return jsonify({
            'success': True,
            'config': config.to_dict()
        }), 200

    except CollectionConfigError as e:
        return jsonify({
            'error': {
                'code': e.code,
                'message': e.message
            }
        }), 404 if e.code == 'SERVER_NOT_FOUND' else 400


@api.route('/servers/<server_id>/collection/stop', methods=['POST'])
@require_tenant
def stop_collection(server_id: str):
    """Stop data collection for a server."""
    try:
        uuid_id = UUID(server_id)
    except ValueError:
        return jsonify({
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid server ID format'
            }
        }), 400

    try:
        service = CollectionConfigService(g.tenant_session)
        config = service.stop_collection(uuid_id)

        return jsonify({
            'success': True,
            'config': config.to_dict()
        }), 200

    except CollectionConfigError as e:
        return jsonify({
            'error': {
                'code': e.code,
                'message': e.message
            }
        }), 404 if e.code == 'SERVER_NOT_FOUND' else 400


@api.route('/servers/health', methods=['GET'])
@require_tenant
def get_all_servers_health():
    """Get health status for all servers."""
    service = HealthService(g.tenant_session)
    health_data = service.get_all_servers_health()

    return jsonify({
        'servers': health_data,
        'total': len(health_data)
    }), 200


@api.route('/servers/<server_id>/health', methods=['GET'])
@require_tenant
def get_server_health(server_id: str):
    """Get health status for a single server."""
    try:
        uuid_id = UUID(server_id)
    except ValueError:
        return jsonify({
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid server ID format'
            }
        }), 400

    service = HealthService(g.tenant_session)
    health_data = service.get_server_health(uuid_id)

    if not health_data:
        return jsonify({
            'error': {
                'code': 'NOT_FOUND',
                'message': f'Server with id {server_id} not found'
            }
        }), 404

    return jsonify(health_data), 200


@api.route('/settings/health-thresholds', methods=['GET'])
@require_tenant
def get_health_thresholds():
    """Get current health thresholds."""
    service = HealthService(g.tenant_session)
    thresholds = service.get_thresholds()

    return jsonify({'thresholds': thresholds}), 200


@api.route('/settings/health-thresholds', methods=['PUT'])
@require_tenant
def update_health_thresholds():
    """Update health thresholds."""
    data = request.get_json() or {}

    try:
        service = HealthService(g.tenant_session)
        thresholds = service.update_thresholds(
            cpu_warning=data.get('cpu_warning'),
            cpu_critical=data.get('cpu_critical'),
            memory_warning=data.get('memory_warning'),
            memory_critical=data.get('memory_critical'),
            offline_seconds=data.get('offline_seconds'),
        )

        return jsonify({'thresholds': thresholds}), 200

    except ValueError as e:
        return jsonify({
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': str(e)
            }
        }), 400


@api.route('/servers/<server_id>/metrics', methods=['GET'])
@require_tenant
def get_server_metrics(server_id: str):
    """
    Get time series metrics for a server.

    Query params:
        range: Time range (1h, 6h, 24h, 7d, 30d) - default: 24h
        metric: Specific metric (cpu, memory, connections, batch_requests) - default: all

    Returns:
        200: Metrics time series data
        404: Server not found
    """
    try:
        uuid_id = UUID(server_id)
    except ValueError:
        return jsonify({
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid server ID format'
            }
        }), 400

    time_range = request.args.get('range', '24h')
    metric = request.args.get('metric')

    # Validate time range
    valid_ranges = ['1h', '6h', '24h', '7d', '30d']
    if time_range not in valid_ranges:
        return jsonify({
            'error': {
                'code': 'INVALID_RANGE',
                'message': f'Invalid time range. Must be one of: {", ".join(valid_ranges)}'
            }
        }), 400

    # Validate metric if provided
    valid_metrics = ['cpu', 'memory', 'connections', 'batch_requests']
    if metric and metric not in valid_metrics:
        return jsonify({
            'error': {
                'code': 'INVALID_METRIC',
                'message': f'Invalid metric. Must be one of: {", ".join(valid_metrics)}'
            }
        }), 400

    try:
        service = MetricsService(g.tenant_session)
        data = service.get_metrics(uuid_id, time_range, metric)

        return jsonify(data), 200

    except MetricsServiceError as e:
        return jsonify({
            'error': {
                'code': e.code,
                'message': e.message
            }
        }), 404 if e.code == 'NOT_FOUND' else 400


@api.route('/servers/<server_id>/metrics/latest', methods=['GET'])
@require_tenant
def get_server_latest_snapshot(server_id: str):
    """Get the latest snapshot for a server."""
    try:
        uuid_id = UUID(server_id)
    except ValueError:
        return jsonify({
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid server ID format'
            }
        }), 400

    try:
        service = MetricsService(g.tenant_session)
        snapshot = service.get_latest_snapshot(uuid_id)

        if not snapshot:
            return jsonify({'snapshot': None}), 200

        return jsonify({'snapshot': snapshot}), 200

    except MetricsServiceError as e:
        return jsonify({
            'error': {
                'code': e.code,
                'message': e.message
            }
        }), 404 if e.code == 'NOT_FOUND' else 400


# Query Collection Endpoints

@api.route('/servers/<server_id>/query-collection/start', methods=['POST'])
@require_tenant
def start_query_collection(server_id: str):
    """Start query collection for a server."""
    try:
        uuid_id = UUID(server_id)
    except ValueError:
        return jsonify({
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid server ID format'
            }
        }), 400

    try:
        service = CollectionConfigService(g.tenant_session)
        config = service.start_query_collection(uuid_id)

        return jsonify({
            'success': True,
            'config': config.to_dict()
        }), 200

    except CollectionConfigError as e:
        return jsonify({
            'error': {
                'code': e.code,
                'message': e.message
            }
        }), 404 if e.code == 'SERVER_NOT_FOUND' else 400


@api.route('/servers/<server_id>/query-collection/stop', methods=['POST'])
@require_tenant
def stop_query_collection(server_id: str):
    """Stop query collection for a server."""
    try:
        uuid_id = UUID(server_id)
    except ValueError:
        return jsonify({
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid server ID format'
            }
        }), 400

    try:
        service = CollectionConfigService(g.tenant_session)
        config = service.stop_query_collection(uuid_id)

        return jsonify({
            'success': True,
            'config': config.to_dict()
        }), 200

    except CollectionConfigError as e:
        return jsonify({
            'error': {
                'code': e.code,
                'message': e.message
            }
        }), 404 if e.code == 'SERVER_NOT_FOUND' else 400


@api.route('/servers/<server_id>/query-collection/config', methods=['PUT'])
@require_tenant
def update_query_collection_config(server_id: str):
    """Update query collection config for a server."""
    try:
        uuid_id = UUID(server_id)
    except ValueError:
        return jsonify({
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid server ID format'
            }
        }), 400

    data = request.get_json() or {}

    try:
        service = CollectionConfigService(g.tenant_session)
        config = service.update_query_config(
            server_id=uuid_id,
            query_collection_interval=data.get('query_collection_interval'),
            query_min_duration_ms=data.get('query_min_duration_ms'),
            query_filter_database=data.get('query_filter_database'),
            query_filter_login=data.get('query_filter_login'),
            query_filter_user=data.get('query_filter_user'),
            query_filter_text_include=data.get('query_filter_text_include'),
            query_filter_text_exclude=data.get('query_filter_text_exclude'),
        )

        return jsonify(config.to_dict()), 200

    except CollectionConfigValidationError as e:
        return jsonify({
            'error': {
                'code': e.code,
                'message': e.message,
                'field': e.field
            }
        }), 400
    except CollectionConfigError as e:
        return jsonify({
            'error': {
                'code': e.code,
                'message': e.message
            }
        }), 404 if e.code == 'SERVER_NOT_FOUND' else 400


@api.route('/servers/<server_id>/running-queries', methods=['GET'])
@require_tenant
def get_running_queries(server_id: str):
    """
    Get running queries history for a server.

    Query params:
        range: Time range (1h, 6h, 24h, 7d, 30d) - default: 1h
        limit: Maximum number of records - default: 100

    Returns:
        200: Running queries data
        404: Server not found
    """
    try:
        uuid_id = UUID(server_id)
    except ValueError:
        return jsonify({
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid server ID format'
            }
        }), 400

    time_range = request.args.get('range', '1h')
    limit = request.args.get('limit', 100, type=int)

    # Validate time range
    valid_ranges = ['1h', '6h', '24h', '7d', '30d']
    if time_range not in valid_ranges:
        return jsonify({
            'error': {
                'code': 'INVALID_RANGE',
                'message': f'Invalid time range. Must be one of: {", ".join(valid_ranges)}'
            }
        }), 400

    # Validate limit
    if limit < 1 or limit > 1000:
        return jsonify({
            'error': {
                'code': 'INVALID_LIMIT',
                'message': 'Limit must be between 1 and 1000'
            }
        }), 400

    service = RunningQueriesService(g.tenant_session)
    data = service.get_running_queries(uuid_id, time_range, limit)

    return jsonify(data), 200


@api.route('/servers/<server_id>/running-queries/latest', methods=['GET'])
@require_tenant
def get_latest_running_queries(server_id: str):
    """Get the most recent running queries snapshot for a server."""
    try:
        uuid_id = UUID(server_id)
    except ValueError:
        return jsonify({
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid server ID format'
            }
        }), 400

    service = RunningQueriesService(g.tenant_session)
    data = service.get_latest_queries(uuid_id)

    return jsonify(data), 200


@api.route('/running-queries', methods=['GET'])
@require_tenant
def get_all_running_queries():
    """
    Get running queries across all servers.

    Query params:
        server_id: Optional server UUID to filter by specific server
        range: Time range (1h, 6h, 24h, 7d, 30d) - default: 1h
        limit: Maximum number of records - default: 500

    Returns:
        200: Running queries data with server info
    """
    server_id = request.args.get('server_id')
    time_range = request.args.get('range', '1h')
    limit = request.args.get('limit', 500, type=int)

    # Validate time range
    valid_ranges = ['1h', '6h', '24h', '7d', '30d']
    if time_range not in valid_ranges:
        return jsonify({
            'error': {
                'code': 'INVALID_RANGE',
                'message': f'Invalid time range. Must be one of: {", ".join(valid_ranges)}'
            }
        }), 400

    # Validate limit
    if limit < 1 or limit > 1000:
        return jsonify({
            'error': {
                'code': 'INVALID_LIMIT',
                'message': 'Limit must be between 1 and 1000'
            }
        }), 400

    # Parse server_id if provided
    uuid_server_id = None
    if server_id:
        try:
            uuid_server_id = UUID(server_id)
        except ValueError:
            return jsonify({
                'error': {
                    'code': 'INVALID_ID',
                    'message': 'Invalid server ID format'
                }
            }), 400

    service = RunningQueriesService(g.tenant_session)
    data = service.get_all_running_queries(
        server_id=uuid_server_id,
        time_range=time_range,
        limit=limit
    )

    return jsonify(data), 200
