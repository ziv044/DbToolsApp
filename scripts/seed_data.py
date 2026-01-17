"""Seed initial data for development."""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import create_app
from app.extensions import db
from app.models import Tenant


def seed_demo_tenant():
    """Create demo tenant if it doesn't exist."""
    app = create_app('development')

    with app.app_context():
        # Check if demo tenant exists
        existing = Tenant.query.filter_by(slug='demo').first()
        if existing:
            print(f"Demo tenant already exists: {existing}")
            return existing

        # Create demo tenant
        tenant = Tenant(
            name='Demo Company',
            slug='demo',
            status='active',
            settings={
                'timezone': 'UTC',
                'retention_days': 90
            }
        )
        db.session.add(tenant)
        db.session.commit()

        print(f"Created demo tenant: {tenant}")
        print(f"  ID: {tenant.id}")
        print(f"  Slug: {tenant.slug}")
        print(f"  Status: {tenant.status}")
        return tenant


if __name__ == '__main__':
    seed_demo_tenant()
