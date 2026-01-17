"""Tenant database provisioning and management."""
import os
from pathlib import Path

from flask import current_app
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker
from alembic.config import Config
from alembic import command


class TenantManager:
    """Manages tenant database provisioning and connections."""

    _engines = {}
    _sessions = {}

    def get_tenant_db_url(self, slug: str) -> str:
        """Generate database URL for a tenant."""
        host = current_app.config['TENANT_DB_HOST']
        port = current_app.config['TENANT_DB_PORT']
        user = current_app.config['TENANT_DB_USER']
        password = current_app.config['TENANT_DB_PASSWORD']
        return f"postgresql://{user}:{password}@{host}:{port}/dbtools_tenant_{slug}"

    def get_engine(self, slug: str):
        """Get or create SQLAlchemy engine for tenant."""
        if slug not in self._engines:
            url = self.get_tenant_db_url(slug)
            self._engines[slug] = create_engine(url)
        return self._engines[slug]

    def get_session(self, slug: str):
        """Get scoped session for tenant database."""
        if slug not in self._sessions:
            engine = self.get_engine(slug)
            session_factory = sessionmaker(bind=engine)
            self._sessions[slug] = scoped_session(session_factory)
        return self._sessions[slug]

    def provision_database(self, slug: str) -> None:
        """Create new tenant database."""
        db_name = f"dbtools_tenant_{slug}"

        # Connect to postgres database to create new database
        host = current_app.config['TENANT_DB_HOST']
        port = current_app.config['TENANT_DB_PORT']
        user = current_app.config['TENANT_DB_USER']
        password = current_app.config['TENANT_DB_PASSWORD']
        postgres_url = f"postgresql://{user}:{password}@{host}:{port}/postgres"

        engine = create_engine(postgres_url, isolation_level="AUTOCOMMIT")
        with engine.connect() as conn:
            # Check if database exists
            result = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                {"db_name": db_name}
            )
            if result.fetchone():
                raise ValueError(f"Database {db_name} already exists")

            # Create database
            conn.execute(text(f'CREATE DATABASE "{db_name}"'))

        engine.dispose()

    def run_migrations(self, slug: str) -> None:
        """Run tenant migrations on database using Alembic."""
        tenant_url = self.get_tenant_db_url(slug)

        # Get path to migrations_tenant directory
        backend_dir = Path(__file__).parent.parent.parent
        migrations_dir = backend_dir / 'migrations_tenant'
        alembic_ini = migrations_dir / 'alembic.ini'

        # Configure Alembic
        alembic_cfg = Config(str(alembic_ini))
        alembic_cfg.set_main_option('script_location', str(migrations_dir))

        # Set the database URL via environment variable
        os.environ['TENANT_DB_URL'] = tenant_url

        try:
            # Run migrations to head
            command.upgrade(alembic_cfg, 'head')
        finally:
            # Clean up environment variable
            if 'TENANT_DB_URL' in os.environ:
                del os.environ['TENANT_DB_URL']

    def get_migration_status(self, slug: str) -> dict:
        """Get migration status for a tenant database."""
        tenant_url = self.get_tenant_db_url(slug)
        engine = create_engine(tenant_url)

        with engine.connect() as conn:
            # Check if alembic_version table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'alembic_version'
                )
            """))
            has_alembic = result.scalar()

            if not has_alembic:
                return {'current_revision': None, 'has_migrations': False}

            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            row = result.fetchone()
            current = row[0] if row else None

        engine.dispose()
        return {'current_revision': current, 'has_migrations': True}

    def drop_database(self, slug: str) -> None:
        """Drop tenant database (for cleanup/testing)."""
        db_name = f"dbtools_tenant_{slug}"

        # Clean up cached engines/sessions
        if slug in self._engines:
            self._engines[slug].dispose()
            del self._engines[slug]
        if slug in self._sessions:
            self._sessions[slug].remove()
            del self._sessions[slug]

        # Connect to postgres database to drop
        host = current_app.config['TENANT_DB_HOST']
        port = current_app.config['TENANT_DB_PORT']
        user = current_app.config['TENANT_DB_USER']
        password = current_app.config['TENANT_DB_PASSWORD']
        postgres_url = f"postgresql://{user}:{password}@{host}:{port}/postgres"

        engine = create_engine(postgres_url, isolation_level="AUTOCOMMIT")
        with engine.connect() as conn:
            # Terminate connections to database
            conn.execute(text(f"""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = '{db_name}'
            """))
            # Drop database
            conn.execute(text(f'DROP DATABASE IF EXISTS "{db_name}"'))

        engine.dispose()

    def provision_tenant(self, slug: str) -> None:
        """Full provisioning: create database and run migrations."""
        try:
            self.provision_database(slug)
            self.run_migrations(slug)
        except Exception as e:
            # Rollback: try to drop the database if it was created
            try:
                self.drop_database(slug)
            except Exception:
                pass  # Ignore cleanup errors
            raise e


tenant_manager = TenantManager()
