"""Unit tests for tenant middleware."""
import pytest
from flask import g
from app.middleware.tenant import TenantMiddleware


class TestTenantMiddlewareExclusions:
    """Test path exclusion logic."""

    def test_health_endpoint_excluded(self):
        """Test /api/health is excluded."""
        middleware = TenantMiddleware()
        assert middleware._is_excluded('/api/health') is True

    def test_tenants_endpoint_excluded(self):
        """Test /api/tenants is excluded."""
        middleware = TenantMiddleware()
        assert middleware._is_excluded('/api/tenants') is True

    def test_tenants_subpath_excluded(self):
        """Test /api/tenants/slug is excluded."""
        middleware = TenantMiddleware()
        assert middleware._is_excluded('/api/tenants/demo') is True

    def test_other_endpoints_not_excluded(self):
        """Test other endpoints are not excluded."""
        middleware = TenantMiddleware()
        assert middleware._is_excluded('/api/servers') is False
        assert middleware._is_excluded('/api/policies') is False


class TestTenantMiddlewareIntegration:
    """Integration tests for tenant middleware."""

    def test_excluded_path_skips_middleware(self, client):
        """Test excluded paths don't require tenant header."""
        response = client.get('/api/health')
        assert response.status_code == 200

    def test_missing_header_returns_400(self, client):
        """Test missing X-Tenant-Slug header returns 400."""
        response = client.get('/api/test-tenant-required')
        assert response.status_code == 400
        data = response.get_json()
        assert data['error']['code'] == 'MISSING_TENANT'

    def test_unknown_tenant_returns_404(self, client):
        """Test unknown tenant slug returns 404."""
        response = client.get(
            '/api/test-tenant-required',
            headers={'X-Tenant-Slug': 'nonexistent'}
        )
        assert response.status_code == 404
        data = response.get_json()
        assert data['error']['code'] == 'TENANT_NOT_FOUND'

    def test_suspended_tenant_returns_403(self, app, client):
        """Test suspended tenant returns 403."""
        from app.extensions import db
        from app.models import Tenant

        with app.app_context():
            # Create a suspended tenant
            tenant = Tenant(name='Suspended', slug='suspended-tenant', status='suspended')
            db.session.add(tenant)
            db.session.commit()

        response = client.get(
            '/api/test-tenant-required',
            headers={'X-Tenant-Slug': 'suspended-tenant'}
        )
        assert response.status_code == 403
        data = response.get_json()
        assert data['error']['code'] == 'TENANT_SUSPENDED'

    def test_valid_tenant_sets_context(self, app, client):
        """Test valid tenant sets g.tenant."""
        from app.extensions import db
        from app.models import Tenant

        with app.app_context():
            # Create an active tenant
            tenant = Tenant(name='Active', slug='active-tenant', status='active')
            db.session.add(tenant)
            db.session.commit()

        response = client.get(
            '/api/test-tenant-required',
            headers={'X-Tenant-Slug': 'active-tenant'}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['tenant'] == 'active-tenant'
