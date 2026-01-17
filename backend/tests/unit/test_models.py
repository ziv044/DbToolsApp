import pytest
from app.models.system import Tenant


class TestTenantSlugValidation:
    """Test Tenant slug validation."""

    def test_valid_slug_lowercase(self):
        """Valid lowercase slug."""
        assert Tenant.validate_slug('demo-tenant') is True

    def test_valid_slug_with_numbers(self):
        """Valid slug with numbers."""
        assert Tenant.validate_slug('tenant123') is True

    def test_valid_slug_minimum_length(self):
        """Valid slug at minimum length (3 chars)."""
        assert Tenant.validate_slug('abc') is True

    def test_valid_slug_maximum_length(self):
        """Valid slug at maximum length (50 chars)."""
        slug = 'a' * 50
        assert Tenant.validate_slug(slug) is True

    def test_invalid_slug_too_short(self):
        """Invalid slug - too short."""
        assert Tenant.validate_slug('ab') is False

    def test_invalid_slug_too_long(self):
        """Invalid slug - too long."""
        slug = 'a' * 51
        assert Tenant.validate_slug(slug) is False

    def test_invalid_slug_starts_with_hyphen(self):
        """Invalid slug - starts with hyphen."""
        assert Tenant.validate_slug('-demo') is False

    def test_invalid_slug_ends_with_hyphen(self):
        """Invalid slug - ends with hyphen."""
        assert Tenant.validate_slug('demo-') is False

    def test_invalid_slug_uppercase(self):
        """Uppercase is converted to lowercase, then validated."""
        # The validation should work with uppercase input
        assert Tenant.validate_slug('DEMO') is True

    def test_invalid_slug_special_chars(self):
        """Invalid slug - special characters."""
        assert Tenant.validate_slug('demo_tenant') is False
        assert Tenant.validate_slug('demo.tenant') is False
        assert Tenant.validate_slug('demo@tenant') is False

    def test_invalid_slug_empty(self):
        """Invalid slug - empty string."""
        assert Tenant.validate_slug('') is False

    def test_invalid_slug_none(self):
        """Invalid slug - None."""
        assert Tenant.validate_slug(None) is False


class TestTenantModel:
    """Test Tenant model CRUD operations."""

    def test_tenant_creation(self, app):
        """Test creating a tenant."""
        from app.extensions import db

        with app.app_context():
            tenant = Tenant(name='Demo Tenant', slug='demo')
            db.session.add(tenant)
            db.session.commit()

            assert tenant.id is not None
            assert tenant.name == 'Demo Tenant'
            assert tenant.slug == 'demo'
            assert tenant.status == 'active'
            assert tenant.created_at is not None

    def test_tenant_slug_uniqueness(self, app):
        """Test that slugs must be unique."""
        from sqlalchemy.exc import IntegrityError
        from app.extensions import db

        with app.app_context():
            tenant1 = Tenant(name='Tenant 1', slug='unique-slug')
            db.session.add(tenant1)
            db.session.commit()

            tenant2 = Tenant(name='Tenant 2', slug='unique-slug')
            db.session.add(tenant2)

            with pytest.raises(IntegrityError):
                db.session.commit()

    def test_tenant_slug_lowercase_conversion(self, app):
        """Test that slugs are converted to lowercase."""
        from app.extensions import db

        with app.app_context():
            tenant = Tenant(name='Upper Case', slug='UPPERCASE')
            db.session.add(tenant)
            db.session.commit()

            assert tenant.slug == 'uppercase'

    def test_tenant_invalid_slug_raises_error(self, app):
        """Test that invalid slugs raise ValueError."""
        from app.extensions import db

        with app.app_context():
            tenant = Tenant(name='Invalid', slug='-invalid-')

            with pytest.raises(ValueError):
                db.session.add(tenant)
                db.session.flush()
