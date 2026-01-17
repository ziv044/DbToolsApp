"""Server group management API endpoints."""
from flask import request, jsonify, g
from uuid import UUID

from app.api import api
from app.middleware import require_tenant
from app.models.tenant import PolicyDeployment
from app.services.group_service import (
    GroupService,
    GroupValidationError,
    GroupNotFoundError,
    ServerNotFoundError,
    CreateGroupInput,
    UpdateGroupInput
)


@api.route('/groups', methods=['GET'])
@require_tenant
def list_groups():
    """List all server groups for the current tenant."""
    service = GroupService(g.tenant_session)
    groups = service.get_all()

    return jsonify({
        'groups': [g.to_dict() for g in groups],
        'total': len(groups)
    })


@api.route('/groups', methods=['POST'])
@require_tenant
def create_group():
    """Create a new server group."""
    data = request.get_json() or {}

    try:
        input = CreateGroupInput(
            name=data.get('name', ''),
            description=data.get('description'),
            color=data.get('color')
        )

        service = GroupService(g.tenant_session)
        group = service.create(input)
        g.tenant_session.commit()

        return jsonify(group.to_dict()), 201

    except GroupValidationError as e:
        g.tenant_session.rollback()
        return jsonify({
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': e.message,
                'field': e.field
            }
        }), 400


@api.route('/groups/<group_id>', methods=['GET'])
@require_tenant
def get_group(group_id: str):
    """Get a server group by ID."""
    try:
        uuid_id = UUID(group_id)
    except ValueError:
        return jsonify({
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid group ID format'
            }
        }), 400

    try:
        service = GroupService(g.tenant_session)
        group = service.get_by_id(uuid_id)
        return jsonify(group.to_dict(include_servers=True))

    except GroupNotFoundError:
        return jsonify({
            'error': {
                'code': 'NOT_FOUND',
                'message': f'Group with id {group_id} not found'
            }
        }), 404


@api.route('/groups/<group_id>', methods=['PUT'])
@require_tenant
def update_group(group_id: str):
    """Update a server group."""
    try:
        uuid_id = UUID(group_id)
    except ValueError:
        return jsonify({
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid group ID format'
            }
        }), 400

    data = request.get_json() or {}

    try:
        input = UpdateGroupInput(
            name=data.get('name'),
            description=data.get('description'),
            color=data.get('color')
        )

        service = GroupService(g.tenant_session)
        group = service.update(uuid_id, input)
        g.tenant_session.commit()

        return jsonify(group.to_dict())

    except GroupNotFoundError:
        return jsonify({
            'error': {
                'code': 'NOT_FOUND',
                'message': f'Group with id {group_id} not found'
            }
        }), 404
    except GroupValidationError as e:
        g.tenant_session.rollback()
        return jsonify({
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': e.message,
                'field': e.field
            }
        }), 400


@api.route('/groups/<group_id>', methods=['DELETE'])
@require_tenant
def delete_group(group_id: str):
    """Delete a server group."""
    try:
        uuid_id = UUID(group_id)
    except ValueError:
        return jsonify({
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid group ID format'
            }
        }), 400

    try:
        service = GroupService(g.tenant_session)
        service.delete(uuid_id)
        g.tenant_session.commit()

        return '', 204

    except GroupNotFoundError:
        return jsonify({
            'error': {
                'code': 'NOT_FOUND',
                'message': f'Group with id {group_id} not found'
            }
        }), 404


@api.route('/groups/<group_id>/servers', methods=['POST'])
@require_tenant
def add_servers_to_group(group_id: str):
    """Add servers to a group."""
    try:
        uuid_id = UUID(group_id)
    except ValueError:
        return jsonify({
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid group ID format'
            }
        }), 400

    data = request.get_json() or {}
    server_ids = data.get('server_ids', [])

    if not server_ids:
        return jsonify({
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'server_ids array is required',
                'field': 'server_ids'
            }
        }), 400

    try:
        # Convert string UUIDs to UUID objects
        uuid_server_ids = [UUID(sid) for sid in server_ids]
    except ValueError:
        return jsonify({
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Invalid server ID format in server_ids',
                'field': 'server_ids'
            }
        }), 400

    try:
        service = GroupService(g.tenant_session)
        group = service.add_servers(uuid_id, uuid_server_ids)
        g.tenant_session.commit()

        return jsonify(group.to_dict(include_servers=True))

    except GroupNotFoundError:
        return jsonify({
            'error': {
                'code': 'NOT_FOUND',
                'message': f'Group with id {group_id} not found'
            }
        }), 404
    except ServerNotFoundError as e:
        g.tenant_session.rollback()
        return jsonify({
            'error': {
                'code': 'SERVER_NOT_FOUND',
                'message': str(e)
            }
        }), 404


@api.route('/groups/<group_id>/servers/<server_id>', methods=['DELETE'])
@require_tenant
def remove_server_from_group(group_id: str, server_id: str):
    """Remove a server from a group."""
    try:
        uuid_group_id = UUID(group_id)
        uuid_server_id = UUID(server_id)
    except ValueError:
        return jsonify({
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid group or server ID format'
            }
        }), 400

    try:
        service = GroupService(g.tenant_session)
        group = service.remove_server(uuid_group_id, uuid_server_id)
        g.tenant_session.commit()

        return jsonify(group.to_dict(include_servers=True))

    except GroupNotFoundError:
        return jsonify({
            'error': {
                'code': 'NOT_FOUND',
                'message': f'Group with id {group_id} not found'
            }
        }), 404
    except ServerNotFoundError as e:
        return jsonify({
            'error': {
                'code': 'SERVER_NOT_FOUND',
                'message': str(e)
            }
        }), 404


@api.route('/groups/<group_id>/policies', methods=['GET'])
@require_tenant
def get_group_policies(group_id: str):
    """Get all policies deployed to a group.

    Returns:
        List of deployed policies with deployment info
    """
    try:
        uuid_id = UUID(group_id)
    except ValueError:
        return jsonify({
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid group ID format'
            }
        }), 400

    try:
        service = GroupService(g.tenant_session)
        group = service.get_by_id(uuid_id)

        # Get deployments for this group
        deployments = g.tenant_session.query(PolicyDeployment).filter(
            PolicyDeployment.group_id == uuid_id
        ).order_by(PolicyDeployment.deployed_at.desc()).all()

        return jsonify({
            'group_id': str(uuid_id),
            'group_name': group.name,
            'policies': [d.to_dict(include_policy=True) for d in deployments],
            'total': len(deployments),
        })

    except GroupNotFoundError:
        return jsonify({
            'error': {
                'code': 'NOT_FOUND',
                'message': f'Group with id {group_id} not found'
            }
        }), 404
