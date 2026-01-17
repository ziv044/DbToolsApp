import pytest
from flask import g
from app import create_app
from app.extensions import db


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app('testing')

    # Add test endpoint that requires tenant
    @app.route('/api/test-tenant-required')
    def test_tenant_required():
        tenant = getattr(g, 'tenant', None)
        if tenant:
            return {'tenant': tenant.slug}
        return {'tenant': None}

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()
