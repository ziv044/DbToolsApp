"""Run pending migrations on all active tenant databases."""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import create_app
from app.extensions import db
from app.models import Tenant
from app.core import tenant_manager


def migrate_all_tenants(dry_run: bool = False):
    """Run migrations on all active tenant databases.

    Args:
        dry_run: If True, only show what would be done without executing.
    """
    app = create_app('development')

    with app.app_context():
        tenants = Tenant.query.filter_by(status='active').all()

        if not tenants:
            print("No active tenants found.")
            return

        print(f"Found {len(tenants)} active tenant(s)")
        print("-" * 50)

        success_count = 0
        error_count = 0

        for tenant in tenants:
            print(f"\nTenant: {tenant.slug}")

            if dry_run:
                print("  [DRY RUN] Would run migrations")
                continue

            try:
                # Get current status
                status = tenant_manager.get_migration_status(tenant.slug)
                print(f"  Current revision: {status.get('current_revision', 'None')}")

                # Run migrations
                tenant_manager.run_migrations(tenant.slug)

                # Get new status
                new_status = tenant_manager.get_migration_status(tenant.slug)
                print(f"  New revision: {new_status.get('current_revision', 'None')}")
                print("  Status: SUCCESS")
                success_count += 1

            except Exception as e:
                print(f"  Status: ERROR - {str(e)}")
                error_count += 1

        print("\n" + "=" * 50)
        print(f"Summary: {success_count} succeeded, {error_count} failed")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Run migrations on all tenant databases')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done')
    args = parser.parse_args()

    migrate_all_tenants(dry_run=args.dry_run)


if __name__ == '__main__':
    main()
