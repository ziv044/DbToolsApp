"""API routes for policy management."""
from uuid import UUID
from flask import request, jsonify, g

from app.api import api
from app.middleware import require_tenant
from app.models.tenant import Policy, PolicyDeployment, ServerGroup
from app.services.policy_service import PolicyService, PolicyValidationError, POLICY_SCHEMAS


def get_policy_service() -> PolicyService:
    """Get a PolicyService instance with the current tenant session."""
    return PolicyService(g.tenant_session)


@api.route('/policies', methods=['GET'])
@require_tenant
def list_policies():
    """List all policies for the tenant.

    Query params:
        type: Filter by policy type
        active: Filter by active status (true/false)

    Returns:
        JSON list of policies
    """
    policy_type = request.args.get('type')
    active_param = request.args.get('active')

    is_active = None
    if active_param is not None:
        is_active = active_param.lower() == 'true'

    service = get_policy_service()
    policies = service.get_all_policies(policy_type=policy_type, is_active=is_active)

    return jsonify({
        'policies': [p.to_dict() for p in policies],
        'total': len(policies),
    })


@api.route('/policies', methods=['POST'])
@require_tenant
def create_policy():
    """Create a new policy.

    Request body:
        name: Policy name (required)
        type: Policy type (required)
        description: Description (optional)
        configuration: Configuration object (required)
        is_active: Active status (optional, default true)

    Returns:
        Created policy with 201 status
    """
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body required'}), 400

    name = data.get('name')
    policy_type = data.get('type')
    configuration = data.get('configuration', {})
    description = data.get('description')
    is_active = data.get('is_active', True)

    # Validate required fields
    errors = []
    if not name:
        errors.append('name is required')
    if not policy_type:
        errors.append('type is required')
    elif policy_type not in Policy.VALID_TYPES:
        errors.append(f'Invalid type. Must be one of: {Policy.VALID_TYPES}')

    if errors:
        return jsonify({'error': 'Validation failed', 'details': errors}), 400

    service = get_policy_service()

    try:
        policy = service.create_policy(
            name=name,
            policy_type=policy_type,
            configuration=configuration,
            description=description,
            is_active=is_active,
        )
        return jsonify(policy.to_dict()), 201

    except PolicyValidationError as e:
        return jsonify({'error': 'Validation failed', 'details': e.errors}), 400


@api.route('/policies/<uuid:policy_id>', methods=['GET'])
@require_tenant
def get_policy(policy_id: UUID):
    """Get a policy by ID.

    Returns:
        Policy details or 404 if not found
    """
    service = get_policy_service()
    policy = service.get_policy(policy_id)

    if not policy:
        return jsonify({'error': 'Policy not found'}), 404

    return jsonify(policy.to_dict(include_versions=False))


@api.route('/policies/<uuid:policy_id>', methods=['PUT'])
@require_tenant
def update_policy(policy_id: UUID):
    """Update a policy.

    If configuration changes, creates a new version (immutable versioning).

    Request body (all optional):
        name: New name
        description: New description
        configuration: New configuration (triggers new version)
        is_active: New active status

    Returns:
        Updated policy or 404 if not found
    """
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body required'}), 400

    service = get_policy_service()

    try:
        policy = service.update_policy(
            policy_id=policy_id,
            name=data.get('name'),
            description=data.get('description'),
            configuration=data.get('configuration'),
            is_active=data.get('is_active'),
        )

        if not policy:
            return jsonify({'error': 'Policy not found'}), 404

        return jsonify(policy.to_dict())

    except PolicyValidationError as e:
        return jsonify({'error': 'Validation failed', 'details': e.errors}), 400


@api.route('/policies/<uuid:policy_id>', methods=['DELETE'])
@require_tenant
def delete_policy(policy_id: UUID):
    """Soft-delete a policy.

    Returns:
        Success message or 404 if not found
    """
    service = get_policy_service()
    deleted = service.delete_policy(policy_id)

    if not deleted:
        return jsonify({'error': 'Policy not found'}), 404

    return jsonify({'message': 'Policy deleted successfully'})


@api.route('/policies/<uuid:policy_id>/versions', methods=['GET'])
@require_tenant
def get_policy_versions(policy_id: UUID):
    """Get version history for a policy.

    Returns:
        List of policy versions, newest first
    """
    service = get_policy_service()

    # Check policy exists
    policy = service.get_policy(policy_id)
    if not policy:
        return jsonify({'error': 'Policy not found'}), 404

    versions = service.get_policy_versions(policy_id)

    return jsonify({
        'policy_id': str(policy_id),
        'current_version': policy.version,
        'versions': [v.to_dict() for v in versions],
    })


@api.route('/policies/<uuid:policy_id>/versions/<int:version>', methods=['GET'])
@require_tenant
def get_policy_version(policy_id: UUID, version: int):
    """Get a specific version of a policy.

    Returns:
        Policy version or 404 if not found
    """
    service = get_policy_service()

    # Check policy exists
    policy = service.get_policy(policy_id)
    if not policy:
        return jsonify({'error': 'Policy not found'}), 404

    policy_version = service.get_policy_version(policy_id, version)
    if not policy_version:
        return jsonify({'error': f'Version {version} not found'}), 404

    return jsonify(policy_version.to_dict())


@api.route('/policies/schemas', methods=['GET'])
@require_tenant
def get_schemas():
    """Get configuration schemas for all policy types.

    Returns:
        Dictionary of policy type -> schema
    """
    return jsonify({
        'policy_types': Policy.VALID_TYPES,
        'schemas': POLICY_SCHEMAS,
    })


@api.route('/policies/schemas/<policy_type>', methods=['GET'])
@require_tenant
def get_schema(policy_type: str):
    """Get configuration schema for a specific policy type.

    Returns:
        Schema or 404 if type not found
    """
    if policy_type not in Policy.VALID_TYPES:
        return jsonify({'error': f'Invalid policy type. Must be one of: {Policy.VALID_TYPES}'}), 404

    schema = PolicyService.get_schema(policy_type)
    return jsonify({
        'type': policy_type,
        'schema': schema,
    })


# ============== Policy Deployment Endpoints ==============


@api.route('/policies/<uuid:policy_id>/deploy', methods=['POST'])
@require_tenant
def deploy_policy(policy_id: UUID):
    """Deploy a policy to one or more server groups.

    Request body:
        group_ids: List of group UUIDs to deploy to

    Returns:
        List of created deployments with 201 status
    """
    service = get_policy_service()
    session = g.tenant_session

    # Check policy exists
    policy = service.get_policy(policy_id)
    if not policy:
        return jsonify({'error': 'Policy not found'}), 404

    data = request.get_json()
    if not data or 'group_ids' not in data:
        return jsonify({'error': 'group_ids is required'}), 400

    group_ids = data.get('group_ids', [])
    if not isinstance(group_ids, list) or len(group_ids) == 0:
        return jsonify({'error': 'group_ids must be a non-empty array'}), 400

    # Validate all groups exist
    deployments = []
    errors = []

    for gid in group_ids:
        try:
            group_uuid = UUID(gid) if isinstance(gid, str) else gid
        except (ValueError, AttributeError):
            errors.append(f'Invalid UUID: {gid}')
            continue

        group = session.query(ServerGroup).filter(ServerGroup.id == group_uuid).first()
        if not group:
            errors.append(f'Group not found: {gid}')
            continue

        # Check if already deployed to this group
        existing = session.query(PolicyDeployment).filter(
            PolicyDeployment.policy_id == policy_id,
            PolicyDeployment.group_id == group_uuid
        ).first()

        if existing:
            # Update existing deployment with new version
            existing.policy_version = policy.version
            deployments.append(existing)
        else:
            # Create new deployment
            deployment = PolicyDeployment(
                policy_id=policy_id,
                policy_version=policy.version,
                group_id=group_uuid,
                deployed_by=data.get('deployed_by'),
            )
            session.add(deployment)
            deployments.append(deployment)

    if errors and not deployments:
        return jsonify({'error': 'Deployment failed', 'details': errors}), 400

    session.commit()

    response = {
        'deployments': [d.to_dict(include_group=True) for d in deployments],
        'total': len(deployments),
    }

    if errors:
        response['warnings'] = errors

    return jsonify(response), 201


@api.route('/policies/<uuid:policy_id>/deployments', methods=['GET'])
@require_tenant
def get_policy_deployments(policy_id: UUID):
    """Get all deployments for a policy.

    Returns:
        List of deployments with group info
    """
    service = get_policy_service()
    session = g.tenant_session

    # Check policy exists
    policy = service.get_policy(policy_id)
    if not policy:
        return jsonify({'error': 'Policy not found'}), 404

    deployments = session.query(PolicyDeployment).filter(
        PolicyDeployment.policy_id == policy_id
    ).order_by(PolicyDeployment.deployed_at.desc()).all()

    return jsonify({
        'policy_id': str(policy_id),
        'deployments': [d.to_dict(include_group=True) for d in deployments],
        'total': len(deployments),
    })


@api.route('/policies/<uuid:policy_id>/deployments/<uuid:group_id>', methods=['DELETE'])
@require_tenant
def remove_deployment(policy_id: UUID, group_id: UUID):
    """Remove a policy deployment from a group.

    Returns:
        Success message or 404 if not found
    """
    session = g.tenant_session

    deployment = session.query(PolicyDeployment).filter(
        PolicyDeployment.policy_id == policy_id,
        PolicyDeployment.group_id == group_id
    ).first()

    if not deployment:
        return jsonify({'error': 'Deployment not found'}), 404

    session.delete(deployment)
    session.commit()

    return jsonify({'message': 'Deployment removed successfully'})
