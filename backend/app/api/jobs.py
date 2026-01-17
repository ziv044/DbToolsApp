"""API routes for job scheduler management."""
from uuid import UUID
from flask import request, jsonify, g

from app.api import api
from app.middleware import require_tenant
from app.models.tenant import Job
from app.services.job_service import JobService, JobValidationError


def get_job_service() -> JobService:
    """Get a JobService instance with the current tenant session."""
    return JobService(g.tenant_session)


@api.route('/jobs', methods=['GET'])
@require_tenant
def list_jobs():
    """List all scheduled jobs for the tenant.

    Query params:
        type: Filter by job type
        enabled: Filter by enabled status (true/false)
        limit: Maximum results (default 100)
        offset: Pagination offset (default 0)

    Returns:
        JSON list of jobs with pagination
    """
    job_type = request.args.get('type')
    enabled_param = request.args.get('enabled')
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)

    is_enabled = None
    if enabled_param is not None:
        is_enabled = enabled_param.lower() == 'true'

    service = get_job_service()
    jobs, total = service.get_all_jobs(
        job_type=job_type,
        is_enabled=is_enabled,
        limit=min(limit, 100),
        offset=offset,
    )

    return jsonify({
        'jobs': [service.get_job_with_last_execution(j) for j in jobs],
        'total': total,
        'limit': limit,
        'offset': offset,
    })


@api.route('/jobs', methods=['POST'])
@require_tenant
def create_job():
    """Create a new scheduled job.

    Request body:
        name: Job name (required)
        type: Job type (required)
        schedule_type: Schedule type (required)
        schedule_config: Schedule configuration (required)
        configuration: Job configuration (optional)
        is_enabled: Whether enabled (optional, default true)

    Returns:
        Created job with 201 status
    """
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body required'}), 400

    service = get_job_service()

    try:
        job = service.create_job(
            name=data.get('name', ''),
            job_type=data.get('type', ''),
            schedule_type=data.get('schedule_type', ''),
            schedule_config=data.get('schedule_config', {}),
            configuration=data.get('configuration'),
            is_enabled=data.get('is_enabled', True),
        )
        return jsonify(job.to_dict()), 201

    except JobValidationError as e:
        return jsonify({'error': 'Validation failed', 'details': e.errors}), 400


@api.route('/jobs/<uuid:job_id>', methods=['GET'])
@require_tenant
def get_job(job_id: UUID):
    """Get a job by ID with recent executions.

    Returns:
        Job details with recent execution history
    """
    service = get_job_service()
    job = service.get_job(job_id)

    if not job:
        return jsonify({'error': 'Job not found'}), 404

    result = service.get_job_with_last_execution(job)

    # Include recent executions
    executions, _ = service.get_job_executions(job_id, limit=10)
    result['recent_executions'] = [e.to_dict() for e in executions]

    return jsonify(result)


@api.route('/jobs/<uuid:job_id>', methods=['PUT'])
@require_tenant
def update_job(job_id: UUID):
    """Update a job.

    Request body (all optional):
        name: New name
        configuration: New configuration
        schedule_type: New schedule type
        schedule_config: New schedule config
        is_enabled: New enabled status

    Returns:
        Updated job or 404 if not found
    """
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body required'}), 400

    service = get_job_service()

    try:
        job = service.update_job(
            job_id=job_id,
            name=data.get('name'),
            configuration=data.get('configuration'),
            schedule_type=data.get('schedule_type'),
            schedule_config=data.get('schedule_config'),
            is_enabled=data.get('is_enabled'),
        )

        if not job:
            return jsonify({'error': 'Job not found'}), 404

        return jsonify(job.to_dict())

    except JobValidationError as e:
        return jsonify({'error': 'Validation failed', 'details': e.errors}), 400


@api.route('/jobs/<uuid:job_id>', methods=['DELETE'])
@require_tenant
def delete_job(job_id: UUID):
    """Delete a job.

    Returns:
        Success message or 404 if not found
    """
    service = get_job_service()
    deleted = service.delete_job(job_id)

    if not deleted:
        return jsonify({'error': 'Job not found'}), 404

    return jsonify({'message': 'Job deleted successfully'})


@api.route('/jobs/<uuid:job_id>/run', methods=['POST'])
@require_tenant
def run_job_now(job_id: UUID):
    """Trigger immediate execution of a job.

    Sets the job's next_run_at to now, causing the scheduler
    to pick it up on the next poll.

    Returns:
        Job with updated next_run_at
    """
    service = get_job_service()
    job = service.run_job_now(job_id)

    if not job:
        return jsonify({'error': 'Job not found'}), 404

    return jsonify({
        'message': 'Job queued for immediate execution',
        'job': job.to_dict(),
    })


@api.route('/jobs/<uuid:job_id>/enable', methods=['POST'])
@require_tenant
def enable_job(job_id: UUID):
    """Enable a disabled job.

    Returns:
        Updated job with new next_run_at
    """
    service = get_job_service()
    job = service.enable_job(job_id)

    if not job:
        return jsonify({'error': 'Job not found'}), 404

    return jsonify(job.to_dict())


@api.route('/jobs/<uuid:job_id>/disable', methods=['POST'])
@require_tenant
def disable_job(job_id: UUID):
    """Disable a job (stops scheduling).

    Returns:
        Updated job with next_run_at set to null
    """
    service = get_job_service()
    job = service.disable_job(job_id)

    if not job:
        return jsonify({'error': 'Job not found'}), 404

    return jsonify(job.to_dict())


@api.route('/jobs/<uuid:job_id>/executions', methods=['GET'])
@require_tenant
def get_job_executions(job_id: UUID):
    """Get execution history for a job.

    Query params:
        limit: Maximum results (default 50)
        offset: Pagination offset (default 0)
        status: Filter by status

    Returns:
        Paginated list of executions
    """
    service = get_job_service()

    # Check job exists
    job = service.get_job(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    status = request.args.get('status')

    executions, total = service.get_job_executions(
        job_id=job_id,
        limit=min(limit, 100),
        offset=offset,
        status=status,
    )

    return jsonify({
        'job_id': str(job_id),
        'executions': [e.to_dict(include_server=True) for e in executions],
        'total': total,
        'limit': limit,
        'offset': offset,
    })


@api.route('/jobs/<uuid:job_id>/executions/<uuid:execution_id>', methods=['GET'])
@require_tenant
def get_execution(job_id: UUID, execution_id: UUID):
    """Get details of a specific execution.

    Returns:
        Execution details with full result data
    """
    service = get_job_service()

    # Check job exists
    job = service.get_job(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    execution = service.get_execution(execution_id)
    if not execution or execution.job_id != job_id:
        return jsonify({'error': 'Execution not found'}), 404

    return jsonify(execution.to_dict(include_job=True, include_server=True))
