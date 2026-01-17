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
