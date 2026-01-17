"""Tenant context middleware."""
import logging
import uuid
from functools import wraps

from flask import request, g, jsonify

from app.extensions import db
from app.models import Tenant
from app.core import tenant_manager

logger = logging.getLogger(__name__)


class TenantMiddleware:
    """Middleware to resolve and validate tenant context from request headers."""

    EXCLUDED_PATHS = ['/api/health', '/api/tenants']

    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize middleware with Flask app."""
        app.before_request(self.resolve_tenant)
        app.teardown_request(self.cleanup_tenant)

    def _is_excluded(self, path: str) -> bool:
        """Check if path is excluded from tenant requirement."""
        return any(
            path == excluded or path.startswith(excluded + '/')
            for excluded in self.EXCLUDED_PATHS
        )

    def resolve_tenant(self):
        """Resolve tenant from X-Tenant-Slug header."""
        # Generate request ID for tracing
        g.request_id = str(uuid.uuid4())[:8]

        # Skip for excluded paths
        if self._is_excluded(request.path):
            logger.debug(f"[{g.request_id}] Skipping tenant check for: {request.path}")
            return None

        slug = request.headers.get('X-Tenant-Slug')

        # Log request with tenant context
        logger.info(f"[{g.request_id}] {request.method} {request.path} tenant={slug or 'none'}")

        if not slug:
            return jsonify({
                'error': {
                    'code': 'MISSING_TENANT',
                    'message': 'X-Tenant-Slug header is required'
                }
            }), 400

        tenant = Tenant.query.filter_by(slug=slug).first()

        if not tenant:
            return jsonify({
                'error': {
                    'code': 'TENANT_NOT_FOUND',
                    'message': f"Tenant '{slug}' not found"
                }
            }), 404

        if tenant.status == 'suspended':
            return jsonify({
                'error': {
                    'code': 'TENANT_SUSPENDED',
                    'message': 'Tenant is suspended'
                }
            }), 403

        # Set tenant context on Flask g object
        g.tenant = tenant
        g.tenant_session = tenant_manager.get_session(slug)

        logger.debug(f"[{g.request_id}] Tenant context established: {slug}")
        return None

    def cleanup_tenant(self, exception=None):
        """Clean up tenant session after request."""
        session = getattr(g, 'tenant_session', None)
        if session:
            try:
                session.remove()
            except Exception as e:
                logger.warning(f"Error cleaning up tenant session: {e}")


def require_tenant(f):
    """Decorator to require tenant context for an endpoint."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(g, 'tenant') or g.tenant is None:
            return jsonify({
                'error': {
                    'code': 'NO_TENANT_CONTEXT',
                    'message': 'Tenant context is required for this endpoint'
                }
            }), 400
        return f(*args, **kwargs)
    return decorated
