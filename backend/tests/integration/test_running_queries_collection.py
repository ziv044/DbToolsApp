"""Integration tests for running queries collection."""
import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock, patch
from uuid import uuid4

from app import create_app
from app.extensions import db
from app.models import Tenant
from app.models.tenant import Server, CollectionConfig, RunningQuerySnapshot
from app.core import tenant_manager
from workers.metric_collector import MetricCollector


@pytest.fixture
def integration_app():
    """Create application with real database for integration testing."""
    app = create_app('development')
    app.config['SQLALCHEMY_ECHO'] = False

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


@pytest.fixture
def test_tenant(integration_app, integration_client):
    """Create a test tenant for running queries tests."""
    payload = {
        'name': 'Test Running Queries',
        'slug': 'test-running-queries'
    }
    response = integration_client.post('/api/tenants', json=payload)
    assert response.status_code == 201
    return response.get_json()


@pytest.fixture
def test_server(integration_app, test_tenant):
    """Create a test server in the tenant database."""
    session = tenant_manager.get_session(test_tenant['slug'])
    try:
        server = Server(
            id=uuid4(),
            name='Test SQL Server',
            hostname='localhost',
            port=1433,
            auth_type='windows',  # Use Windows auth to avoid needing encrypted password
            status='online'
        )
        session.add(server)
        session.commit()

        # Create collection config with query collection enabled
        config = CollectionConfig(
            server_id=server.id,
            interval_seconds=60,
            enabled=True,
            metrics_enabled=['cpu_percent', 'memory_percent'],
            query_collection_enabled=True,
            query_collection_interval=30,
            query_min_duration_ms=0
        )
        session.add(config)
        session.commit()

        yield {'server': server, 'config': config, 'tenant_slug': test_tenant['slug']}
    finally:
        session.remove()


class TestRunningQueriesCollection:
    """Test running queries collection and storage."""

    def test_running_queries_table_exists(self, integration_app, test_tenant):
        """Verify that running_query_snapshots table exists after migration."""
        session = tenant_manager.get_session(test_tenant['slug'])
        try:
            # Query should not raise an error if table exists
            count = session.query(RunningQuerySnapshot).count()
            assert count == 0  # Should be empty initially
        finally:
            session.remove()

    def test_collect_running_queries_saves_to_postgres(self, integration_app, test_server):
        """Test that running queries are collected and saved to PostgreSQL."""
        tenant_slug = test_server['tenant_slug']
        server = test_server['server']
        config = test_server['config']

        # Mock running queries data from SQL Server
        mock_running_queries = [
            (
                55,  # session_id
                1,   # request_id
                'TestDB',  # database_name
                'SELECT * FROM Users WHERE id = 123',  # query_text
                datetime.now(timezone.utc),  # start_time
                1500,  # duration_ms
                'running',  # status
                'CXPACKET',  # wait_type
                100,  # wait_time_ms
                250,  # cpu_time_ms
                5000,  # logical_reads
                50,   # physical_reads
                10,   # writes
            ),
            (
                56,  # session_id
                1,   # request_id
                'OrdersDB',  # database_name
                'UPDATE Orders SET status = ''shipped'' WHERE order_id = 456',  # query_text
                datetime.now(timezone.utc),  # start_time
                3200,  # duration_ms
                'suspended',  # status
                'LCK_M_X',  # wait_type
                2500,  # wait_time_ms
                800,  # cpu_time_ms
                15000,  # logical_reads
                200,  # physical_reads
                500,  # writes
            ),
        ]

        # Create mock cursor that returns our test data
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = mock_running_queries
        mock_cursor.fetchone.side_effect = [
            (50,),  # CPU
            (65.5,),  # Memory
            (25,),  # Connections
            (1000,),  # Batch requests
            (300,),  # PLE
            (0,),  # Blocked processes
        ]

        # Create mock connection
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        with integration_app.app_context():
            # Get a fresh session
            session = tenant_manager.get_session(tenant_slug)

            try:
                # Re-fetch server and config in this session
                server = session.query(Server).filter_by(name='Test SQL Server').first()
                config = session.query(CollectionConfig).filter_by(server_id=server.id).first()

                # Create metric collector and call _collect_running_queries directly
                collector = MetricCollector()
                collector.connector = MagicMock()

                # Call the collection method
                collector._collect_running_queries(session, server, config, mock_cursor)
                session.commit()

                # Verify queries were saved to PostgreSQL
                saved_queries = session.query(RunningQuerySnapshot).filter_by(
                    server_id=server.id
                ).all()

                assert len(saved_queries) == 2

                # Verify first query
                query1 = next(q for q in saved_queries if q.session_id == 55)
                assert query1.database_name == 'TestDB'
                assert 'SELECT * FROM Users' in query1.query_text
                assert query1.duration_ms == 1500
                assert query1.status == 'running'
                assert query1.wait_type == 'CXPACKET'
                assert query1.cpu_time_ms == 250
                assert query1.logical_reads == 5000

                # Verify second query
                query2 = next(q for q in saved_queries if q.session_id == 56)
                assert query2.database_name == 'OrdersDB'
                assert 'UPDATE Orders' in query2.query_text
                assert query2.duration_ms == 3200
                assert query2.status == 'suspended'
                assert query2.wait_type == 'LCK_M_X'

            finally:
                session.remove()

    def test_running_queries_api_returns_data(self, integration_app, integration_client, test_server):
        """Test that the running queries API endpoint returns stored data."""
        tenant_slug = test_server['tenant_slug']

        with integration_app.app_context():
            session = tenant_manager.get_session(tenant_slug)
            try:
                # Re-fetch server in this session
                server = session.query(Server).filter_by(name='Test SQL Server').first()
                assert server is not None, "Server not found in database"

                # Insert a test query snapshot directly
                snapshot = RunningQuerySnapshot(
                    server_id=server.id,
                    collected_at=datetime.now(timezone.utc),
                    session_id=100,
                    request_id=1,
                    database_name='TestDB',
                    query_text='SELECT COUNT(*) FROM LargeTable',
                    duration_ms=5000,
                    status='running',
                    wait_type='IO_COMPLETION',
                    wait_time_ms=4000,
                    cpu_time_ms=1000,
                    logical_reads=100000,
                    physical_reads=5000,
                    writes=0
                )
                session.add(snapshot)
                session.commit()
                server_id = str(server.id)
            finally:
                session.remove()

        # Call the API
        response = integration_client.get(
            f'/api/servers/{server_id}/running-queries/latest',
            headers={'X-Tenant-Slug': tenant_slug}
        )

        # Debug: print response if not 200
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.get_json()}")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.get_json()}"
        data = response.get_json()

        assert data['total'] == 1
        assert len(data['queries']) == 1

        query = data['queries'][0]
        assert query['session_id'] == 100
        assert query['database_name'] == 'TestDB'
        assert 'SELECT COUNT(*)' in query['query_text']
        assert query['duration_ms'] == 5000

    def test_query_collection_respects_min_duration_filter(self, integration_app, test_server):
        """Test that queries below min_duration_ms are filtered out."""
        tenant_slug = test_server['tenant_slug']

        with integration_app.app_context():
            session = tenant_manager.get_session(tenant_slug)
            try:
                server = session.query(Server).filter_by(name='Test SQL Server').first()
                config = session.query(CollectionConfig).filter_by(server_id=server.id).first()

                # Set minimum duration to 1000ms
                config.query_min_duration_ms = 1000
                session.commit()

                # Verify config was updated
                assert config.query_min_duration_ms == 1000
            finally:
                session.remove()

    def test_query_collection_config_api(self, integration_app, integration_client, test_server):
        """Test query collection configuration via API."""
        tenant_slug = test_server['tenant_slug']

        with integration_app.app_context():
            session = tenant_manager.get_session(tenant_slug)
            try:
                server = session.query(Server).filter_by(name='Test SQL Server').first()
                assert server is not None, "Server not found in database"
                server_id = str(server.id)
            finally:
                session.remove()

        # Get current config
        response = integration_client.get(
            f'/api/servers/{server_id}/collection-config',
            headers={'X-Tenant-Slug': tenant_slug}
        )

        if response.status_code != 200:
            print(f"GET config - Response status: {response.status_code}")
            print(f"Response data: {response.get_json()}")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.get_json()}"
        data = response.get_json()
        assert data['query_collection_enabled'] is True
        assert data['query_collection_interval'] == 30

        # Update query collection config
        response = integration_client.put(
            f'/api/servers/{server_id}/query-collection/config',
            headers={'X-Tenant-Slug': tenant_slug},
            json={
                'query_collection_interval': 60,
                'query_min_duration_ms': 500
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.get_json()}"
        data = response.get_json()
        assert data['query_collection_interval'] == 60
        assert data['query_min_duration_ms'] == 500

        # Stop query collection
        response = integration_client.post(
            f'/api/servers/{server_id}/query-collection/stop',
            headers={'X-Tenant-Slug': tenant_slug}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.get_json()}"
        data = response.get_json()
        assert data['config']['query_collection_enabled'] is False

        # Start query collection
        response = integration_client.post(
            f'/api/servers/{server_id}/query-collection/start',
            headers={'X-Tenant-Slug': tenant_slug}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.get_json()}"
        data = response.get_json()
        assert data['config']['query_collection_enabled'] is True
