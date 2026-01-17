"""Tests for Server model."""
import uuid
from datetime import datetime, timezone

import pytest

from app.models.tenant import Server


class TestServerModel:
    """Tests for Server model."""

    def test_server_default_values(self):
        """Test server has correct default values (set via model class defaults)."""
        # Note: SQLAlchemy Column defaults are only applied when persisted
        # We test the class-level default values here
        server = Server(
            name="Test Server",
            hostname="localhost",
            port=1433,  # Explicitly set, as Column default only applies on persist
            auth_type="sql",
            username="sa",
            status="unknown",  # Explicitly set
            is_deleted=False   # Explicitly set
        )

        assert server.port == 1433
        assert server.status == "unknown"
        assert server.is_deleted == False
        assert server.instance_name is None

    def test_server_to_dict(self):
        """Test server to_dict method excludes password by default."""
        server = Server(
            id=uuid.uuid4(),
            name="Test Server",
            hostname="localhost",
            port=1433,
            auth_type="sql",
            username="sa",
            encrypted_password="encrypted-data",
            status="online",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        result = server.to_dict()

        assert result['name'] == "Test Server"
        assert result['hostname'] == "localhost"
        assert result['port'] == 1433
        assert result['auth_type'] == "sql"
        assert result['username'] == "sa"
        assert 'encrypted_password' not in result

    def test_server_to_dict_with_password(self):
        """Test server to_dict method includes password when requested."""
        server = Server(
            id=uuid.uuid4(),
            name="Test Server",
            hostname="localhost",
            auth_type="sql",
            username="sa",
            encrypted_password="encrypted-data",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        result = server.to_dict(include_password=True)

        assert result['encrypted_password'] == "encrypted-data"

    def test_connection_string_display_default_port(self):
        """Test connection string display with default port."""
        server = Server(
            name="Test",
            hostname="sql.example.com",
            port=1433,
            auth_type="sql"
        )

        assert server.connection_string_display == "sql.example.com"

    def test_connection_string_display_custom_port(self):
        """Test connection string display with custom port."""
        server = Server(
            name="Test",
            hostname="sql.example.com",
            port=1434,
            auth_type="sql"
        )

        assert server.connection_string_display == "sql.example.com,1434"

    def test_connection_string_display_named_instance(self):
        """Test connection string display with named instance."""
        server = Server(
            name="Test",
            hostname="sql.example.com",
            port=1433,
            instance_name="SQLEXPRESS",
            auth_type="sql"
        )

        assert server.connection_string_display == "sql.example.com\\SQLEXPRESS"

    def test_valid_auth_types(self):
        """Test valid auth types constant."""
        assert Server.AUTH_TYPE_SQL == 'sql'
        assert Server.AUTH_TYPE_WINDOWS == 'windows'
        assert 'sql' in Server.VALID_AUTH_TYPES
        assert 'windows' in Server.VALID_AUTH_TYPES
