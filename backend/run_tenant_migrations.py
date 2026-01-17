"""Run tenant migrations for all active tenants."""
import os
import sys

# Ensure we can import from app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models.system import Tenant
from app.core.tenant_manager import tenant_manager

def main():
    app = create_app()

    with app.app_context():
        # Get all active tenants
        tenants = Tenant.query.filter_by(status='active').all()

        if not tenants:
            print("No active tenants found")
            return

        for tenant in tenants:
            print(f"Running migrations for tenant: {tenant.slug}")
            try:
                # Check current status
                status = tenant_manager.get_migration_status(tenant.slug)
                print(f"  Current revision: {status['current_revision']}")

                # Run migrations
                tenant_manager.run_migrations(tenant.slug)

                # Check new status
                status = tenant_manager.get_migration_status(tenant.slug)
                print(f"  New revision: {status['current_revision']}")
                print(f"  [OK] Migrations complete for {tenant.slug}")
            except Exception as e:
                print(f"  [ERROR] {e}")

if __name__ == '__main__':
    main()
