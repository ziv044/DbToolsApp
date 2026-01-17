"""Tenant management API endpoints."""
from flask import request, jsonify

from app.api import api
from app.extensions import db
from app.models import Tenant
from app.core import tenant_manager


def error_response(code: str, message: str, status_code: int, details=None):
    """Create standardized error response."""
    response = {
        'error': {
            'code': code,
            'message': message
        }
    }
    if details:
        response['error']['details'] = details
    return jsonify(response), status_code


def tenant_to_dict(tenant: Tenant) -> dict:
    """Convert Tenant model to dictionary."""
    return {
        'id': str(tenant.id),
        'name': tenant.name,
        'slug': tenant.slug,
        'status': tenant.status,
        'settings': tenant.settings,
        'created_at': tenant.created_at.isoformat() if tenant.created_at else None,
        'updated_at': tenant.updated_at.isoformat() if tenant.updated_at else None
    }


@api.route('/tenants', methods=['GET'])
def list_tenants():
    """List all tenants."""
    tenants = Tenant.query.order_by(Tenant.created_at.desc()).all()
    return jsonify([tenant_to_dict(t) for t in tenants])


@api.route('/tenants', methods=['POST'])
def create_tenant():
    """Create a new tenant with database provisioning."""
    data = request.get_json()

    if not data:
        return error_response('VALIDATION_ERROR', 'Request body is required', 400)

    # Validate required fields
    errors = []
    if not data.get('name'):
        errors.append({'field': 'name', 'message': 'Name is required'})
    if not data.get('slug'):
        errors.append({'field': 'slug', 'message': 'Slug is required'})

    if errors:
        return error_response('VALIDATION_ERROR', 'Invalid input', 400, errors)

    slug = data['slug'].lower()

    # Validate slug format
    if not Tenant.validate_slug(slug):
        return error_response(
            'VALIDATION_ERROR',
            'Invalid slug format. Must be 3-50 chars, alphanumeric + hyphens, start and end with alphanumeric.',
            400,
            [{'field': 'slug', 'message': 'Invalid format'}]
        )

    # Check for existing tenant
    existing = Tenant.query.filter_by(slug=slug).first()
    if existing:
        return error_response(
            'CONFLICT',
            f"Tenant with slug '{slug}' already exists",
            409
        )

    try:
        # Create tenant record
        tenant = Tenant(
            name=data['name'],
            slug=slug,
            status='active',
            settings=data.get('settings', {})
        )
        db.session.add(tenant)
        db.session.flush()  # Get ID before committing

        # Provision tenant database
        tenant_manager.provision_tenant(slug)

        db.session.commit()

        return jsonify(tenant_to_dict(tenant)), 201

    except Exception as e:
        db.session.rollback()
        # Try to cleanup database if it was created
        try:
            tenant_manager.drop_database(slug)
        except Exception:
            pass
        return error_response(
            'PROVISIONING_ERROR',
            f'Failed to provision tenant: {str(e)}',
            500
        )


@api.route('/tenants/<slug>', methods=['GET'])
def get_tenant(slug: str):
    """Get tenant by slug."""
    tenant = Tenant.query.filter_by(slug=slug).first()
    if not tenant:
        return error_response('NOT_FOUND', f"Tenant '{slug}' not found", 404)
    return jsonify(tenant_to_dict(tenant))


@api.route('/tenants/<slug>', methods=['DELETE'])
def delete_tenant(slug: str):
    """Soft delete a tenant."""
    tenant = Tenant.query.filter_by(slug=slug).first()
    if not tenant:
        return error_response('NOT_FOUND', f"Tenant '{slug}' not found", 404)

    if tenant.status == 'deleted':
        return error_response('CONFLICT', 'Tenant is already deleted', 409)

    tenant.status = 'suspended'  # Soft delete - mark as suspended
    db.session.commit()

    return jsonify(tenant_to_dict(tenant))
