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


@api.route('/servers', methods=['POST'])
@require_tenant
def create_server():
    """Create a new server."""
    data = request.get_json() or {}

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
        return jsonify(server.to_dict())

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
