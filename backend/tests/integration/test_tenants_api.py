"""Integration tests for tenant API endpoints."""
import pytest
from app import create_app
from app.extensions import db
from app.models import Tenant
from app.core import tenant_manager


@pytest.fixture
def integration_app():
    """Create application with real database for integration testing."""
    app = create_app('development')
    app.config['SQLALCHEMY_ECHO'] = False  # Reduce noise in test output

    with app.app_context():
        db.create_all()
        yield app
        # Cleanup: remove any test tenants
        test_tenants = Tenant.query.filter(Tenant.slug.like('test-%')).all()
        for tenant in test_tenants:
            try:
                tenant_manager.drop_database(tenant.slug)
            except Exception:
                pass
            db.session.delete(tenant)
        db.session.commit()


@pytest.fixture
def integration_client(integration_app):
    """Create test client for integration tests."""
    return integration_app.test_client()


class TestTenantsAPI:
    """Test tenant API endpoints."""

    def test_list_tenants_empty(self, integration_client):
        """Test listing tenants when none exist (except demo)."""
        response = integration_client.get('/api/tenants')
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)

    def test_create_tenant_success(self, integration_client, integration_app):
        """Test creating a new tenant with database provisioning."""
        payload = {
            'name': 'Test Company',
            'slug': 'test-company-1',
            'settings': {'timezone': 'UTC'}
        }
        response = integration_client.post(
            '/api/tenants',
            json=payload,
            content_type='application/json'
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data['name'] == 'Test Company'
        assert data['slug'] == 'test-company-1'
        assert data['status'] == 'active'
        assert 'id' in data
        assert 'created_at' in data

    def test_create_tenant_duplicate_slug(self, integration_client):
        """Test 409 error when slug already exists."""
        payload = {'name': 'First', 'slug': 'test-duplicate'}
        response1 = integration_client.post('/api/tenants', json=payload)
        assert response1.status_code == 201

        payload2 = {'name': 'Second', 'slug': 'test-duplicate'}
        response2 = integration_client.post('/api/tenants', json=payload2)
        assert response2.status_code == 409
        data = response2.get_json()
        assert data['error']['code'] == 'CONFLICT'

    def test_create_tenant_invalid_slug(self, integration_client):
        """Test 400 error for invalid slug format."""
        payload = {'name': 'Bad Slug', 'slug': '-invalid-'}
        response = integration_client.post('/api/tenants', json=payload)

        assert response.status_code == 400
        data = response.get_json()
        assert data['error']['code'] == 'VALIDATION_ERROR'

    def test_create_tenant_missing_name(self, integration_client):
        """Test 400 error when name is missing."""
        payload = {'slug': 'test-no-name'}
        response = integration_client.post('/api/tenants', json=payload)

        assert response.status_code == 400
        data = response.get_json()
        assert data['error']['code'] == 'VALIDATION_ERROR'

    def test_create_tenant_missing_slug(self, integration_client):
        """Test 400 error when slug is missing."""
        payload = {'name': 'No Slug'}
        response = integration_client.post('/api/tenants', json=payload)

        assert response.status_code == 400
        data = response.get_json()
        assert data['error']['code'] == 'VALIDATION_ERROR'

    def test_get_tenant(self, integration_client):
        """Test getting a specific tenant."""
        # Create tenant first
        payload = {'name': 'Get Test', 'slug': 'test-get-tenant'}
        integration_client.post('/api/tenants', json=payload)

        response = integration_client.get('/api/tenants/test-get-tenant')
        assert response.status_code == 200
        data = response.get_json()
        assert data['slug'] == 'test-get-tenant'

    def test_get_tenant_not_found(self, integration_client):
        """Test 404 when tenant doesn't exist."""
        response = integration_client.get('/api/tenants/nonexistent')
        assert response.status_code == 404
        data = response.get_json()
        assert data['error']['code'] == 'NOT_FOUND'

    def test_delete_tenant(self, integration_client):
        """Test soft-deleting a tenant."""
        # Create tenant first
        payload = {'name': 'Delete Test', 'slug': 'test-delete-tenant'}
        integration_client.post('/api/tenants', json=payload)

        response = integration_client.delete('/api/tenants/test-delete-tenant')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'suspended'

    def test_delete_tenant_not_found(self, integration_client):
        """Test 404 when deleting nonexistent tenant."""
        response = integration_client.delete('/api/tenants/nonexistent')
        assert response.status_code == 404
