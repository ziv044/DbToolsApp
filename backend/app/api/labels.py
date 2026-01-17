"""API endpoints for server labels."""
from uuid import UUID
from flask import request, jsonify, g

from app.api import api
from app.middleware import require_tenant
from app.services.label_service import LabelService


@api.route('/labels', methods=['GET'])
@require_tenant
def get_labels():
    """Get all labels.

    Returns:
        JSON with list of labels and total count.
    """
    service = LabelService(g.tenant_session)
    result = service.get_all_labels()
    return jsonify(result), 200


@api.route('/labels', methods=['POST'])
@require_tenant
def create_label():
    """Create a new label.

    Request body:
        name: Label name (required)
        color: Hex color (optional, default #6B7280)

    Returns:
        Created label.
    """
    data = request.get_json()

    if not data or not data.get('name'):
        return jsonify({'error': {'code': 'VALIDATION_ERROR', 'message': 'Name is required'}}), 400

    service = LabelService(g.tenant_session)

    try:
        label = service.create_label(
            name=data['name'],
            color=data.get('color')
        )
        return jsonify(label.to_dict()), 201
    except ValueError as e:
        return jsonify({'error': {'code': 'VALIDATION_ERROR', 'message': str(e)}}), 400


@api.route('/labels/<label_id>', methods=['GET'])
@require_tenant
def get_label(label_id: str):
    """Get a label by ID.

    Args:
        label_id: Label UUID.

    Returns:
        Label data.
    """
    try:
        label_uuid = UUID(label_id)
    except ValueError:
        return jsonify({'error': {'code': 'VALIDATION_ERROR', 'message': 'Invalid label ID'}}), 400

    service = LabelService(g.tenant_session)
    label = service.get_label_by_id(label_uuid)

    if not label:
        return jsonify({'error': {'code': 'NOT_FOUND', 'message': 'Label not found'}}), 404

    return jsonify(label.to_dict()), 200


@api.route('/labels/<label_id>', methods=['PUT'])
@require_tenant
def update_label(label_id: str):
    """Update a label.

    Args:
        label_id: Label UUID.

    Request body:
        name: New label name (optional)
        color: New hex color (optional)

    Returns:
        Updated label.
    """
    try:
        label_uuid = UUID(label_id)
    except ValueError:
        return jsonify({'error': {'code': 'VALIDATION_ERROR', 'message': 'Invalid label ID'}}), 400

    data = request.get_json()
    if not data:
        return jsonify({'error': {'code': 'VALIDATION_ERROR', 'message': 'No data provided'}}), 400

    service = LabelService(g.tenant_session)

    try:
        label = service.update_label(
            label_id=label_uuid,
            name=data.get('name'),
            color=data.get('color')
        )
        return jsonify(label.to_dict()), 200
    except ValueError as e:
        error_message = str(e)
        if 'not found' in error_message.lower():
            return jsonify({'error': {'code': 'NOT_FOUND', 'message': error_message}}), 404
        return jsonify({'error': {'code': 'VALIDATION_ERROR', 'message': error_message}}), 400


@api.route('/labels/<label_id>', methods=['DELETE'])
@require_tenant
def delete_label(label_id: str):
    """Delete a label.

    Args:
        label_id: Label UUID.

    Returns:
        Empty response with 204 status.
    """
    try:
        label_uuid = UUID(label_id)
    except ValueError:
        return jsonify({'error': {'code': 'VALIDATION_ERROR', 'message': 'Invalid label ID'}}), 400

    service = LabelService(g.tenant_session)

    try:
        service.delete_label(label_uuid)
        return '', 204
    except ValueError as e:
        return jsonify({'error': {'code': 'NOT_FOUND', 'message': str(e)}}), 404


@api.route('/servers/<server_id>/labels', methods=['GET'])
@require_tenant
def get_server_labels(server_id: str):
    """Get all labels for a server.

    Args:
        server_id: Server UUID.

    Returns:
        List of labels.
    """
    try:
        server_uuid = UUID(server_id)
    except ValueError:
        return jsonify({'error': {'code': 'VALIDATION_ERROR', 'message': 'Invalid server ID'}}), 400

    service = LabelService(g.tenant_session)
    labels = service.get_server_labels(server_uuid)

    return jsonify({
        'labels': [label.to_dict() for label in labels],
        'total': len(labels)
    }), 200


@api.route('/servers/<server_id>/labels', methods=['POST'])
@require_tenant
def assign_labels_to_server(server_id: str):
    """Assign labels to a server.

    Labels are created automatically if they don't exist.

    Args:
        server_id: Server UUID.

    Request body:
        labels: Array of label names.

    Returns:
        List of assigned labels.
    """
    try:
        server_uuid = UUID(server_id)
    except ValueError:
        return jsonify({'error': {'code': 'VALIDATION_ERROR', 'message': 'Invalid server ID'}}), 400

    data = request.get_json()
    if not data or not data.get('labels'):
        return jsonify({'error': {'code': 'VALIDATION_ERROR', 'message': 'Labels array is required'}}), 400

    label_names = data.get('labels', [])
    if not isinstance(label_names, list):
        return jsonify({'error': {'code': 'VALIDATION_ERROR', 'message': 'Labels must be an array'}}), 400

    service = LabelService(g.tenant_session)

    try:
        labels = service.assign_labels_to_server(server_uuid, label_names)
        return jsonify({
            'labels': [label.to_dict() for label in labels],
            'total': len(labels)
        }), 200
    except ValueError as e:
        error_message = str(e)
        if 'not found' in error_message.lower():
            return jsonify({'error': {'code': 'NOT_FOUND', 'message': error_message}}), 404
        return jsonify({'error': {'code': 'VALIDATION_ERROR', 'message': error_message}}), 400


@api.route('/servers/<server_id>/labels/<label_id>', methods=['DELETE'])
@require_tenant
def remove_label_from_server(server_id: str, label_id: str):
    """Remove a label from a server.

    Args:
        server_id: Server UUID.
        label_id: Label UUID.

    Returns:
        Empty response with 204 status.
    """
    try:
        server_uuid = UUID(server_id)
        label_uuid = UUID(label_id)
    except ValueError:
        return jsonify({'error': {'code': 'VALIDATION_ERROR', 'message': 'Invalid ID format'}}), 400

    service = LabelService(g.tenant_session)

    try:
        service.remove_label_from_server(server_uuid, label_uuid)
        return '', 204
    except ValueError as e:
        return jsonify({'error': {'code': 'NOT_FOUND', 'message': str(e)}}), 404
