"""Tests for SQL Server connector."""
import pytest
from unittest.mock import Mock, patch, MagicMock

from app.connectors.sqlserver import (
    SQLServerConnector,
    SQLServerConnectionError,
    ConnectionTestResult,
    PYODBC_AVAILABLE
)


class TestConnectionTestResult:
    """Tests for ConnectionTestResult dataclass."""

    def test_success_result_to_dict(self):
        """Test successful result conversion to dict."""
        result = ConnectionTestResult(
            success=True,
            version="Microsoft SQL Server 2019",
            edition="Developer",
            product_version="15.0.2000.5",
            has_view_server_state=True,
            is_supported_version=True
        )

        d = result.to_dict()

        assert d['success'] is True
        assert d['version'] == "Microsoft SQL Server 2019"
        assert d['edition'] == "Developer"
        assert d['product_version'] == "15.0.2000.5"
        assert d['has_view_server_state'] is True
        assert d['is_supported_version'] is True
        assert 'error' not in d
        assert 'error_code' not in d

    def test_failure_result_to_dict(self):
        """Test failure result conversion to dict."""
        result = ConnectionTestResult(
            success=False,
            error="Login failed",
            error_code="AUTH_FAILED"
        )

        d = result.to_dict()

        assert d['success'] is False
        assert d['error'] == "Login failed"
        assert d['error_code'] == "AUTH_FAILED"
        assert 'version' not in d


class TestSQLServerConnector:
    """Tests for SQLServerConnector class."""

    @pytest.fixture
    def mock_app(self):
        """Create mock Flask app context."""
        app = Mock()
        app.config = {'SQLSERVER_DRIVER': 'ODBC Driver 18 for SQL Server'}
        return app

    def test_build_connection_string_default_port(self, mock_app):
        """Test connection string with default port."""
        with patch('app.connectors.sqlserver.current_app', mock_app):
            connector = SQLServerConnector()
            conn_str = connector._build_connection_string(
                hostname='localhost',
                port=1433,
                auth_type='sql',
                username='sa',
                password='test123'
            )

        assert 'DRIVER={ODBC Driver 18 for SQL Server}' in conn_str
        assert 'SERVER=localhost,1433' in conn_str
        assert 'DATABASE=master' in conn_str
        assert 'UID=sa' in conn_str
        assert 'PWD=test123' in conn_str
        assert 'TrustServerCertificate=yes' in conn_str

    def test_build_connection_string_custom_port(self, mock_app):
        """Test connection string with custom port."""
        with patch('app.connectors.sqlserver.current_app', mock_app):
            connector = SQLServerConnector()
            conn_str = connector._build_connection_string(
                hostname='db.example.com',
                port=1434,
                auth_type='sql',
                username='sa',
                password='test123'
            )

        assert 'SERVER=db.example.com,1434' in conn_str

    def test_build_connection_string_named_instance(self, mock_app):
        """Test connection string with named instance."""
        with patch('app.connectors.sqlserver.current_app', mock_app):
            connector = SQLServerConnector()
            conn_str = connector._build_connection_string(
                hostname='localhost',
                port=1433,
                instance_name='SQLEXPRESS',
                auth_type='sql',
                username='sa',
                password='test123'
            )

        assert 'SERVER=localhost\\SQLEXPRESS' in conn_str

    def test_build_connection_string_windows_auth(self, mock_app):
        """Test connection string with Windows authentication."""
        with patch('app.connectors.sqlserver.current_app', mock_app):
            connector = SQLServerConnector()
            conn_str = connector._build_connection_string(
                hostname='localhost',
                port=1433,
                auth_type='windows'
            )

        assert 'Trusted_Connection=yes' in conn_str
        assert 'UID=' not in conn_str
        assert 'PWD=' not in conn_str

    def test_build_connection_string_sql_auth_requires_username(self, mock_app):
        """Test that SQL auth requires username."""
        with patch('app.connectors.sqlserver.current_app', mock_app):
            connector = SQLServerConnector()

            with pytest.raises(SQLServerConnectionError) as exc:
                connector._build_connection_string(
                    hostname='localhost',
                    port=1433,
                    auth_type='sql'
                )

            assert 'Username required' in str(exc.value)

    def test_parse_version_2019(self):
        """Test version parsing for SQL Server 2019."""
        connector = SQLServerConnector()
        version_str = "Microsoft SQL Server 2019 (RTM-CU18) (KB5017593) - 15.0.4261.1 (X64)   Sep  5 2022 23:23:00   Developer Edition (64-bit) on Windows 10 Pro 10.0 <X64>"

        major, edition, product_version = connector._parse_version(version_str)

        assert major == 15
        assert edition == "Developer"
        assert product_version == "15.0.4261.1"

    def test_parse_version_2016(self):
        """Test version parsing for SQL Server 2016."""
        connector = SQLServerConnector()
        version_str = "Microsoft SQL Server 2016 (SP2) (KB4052908) - 13.0.5026.0 (X64)   Mar 18 2018   Standard Edition (64-bit)"

        major, edition, product_version = connector._parse_version(version_str)

        assert major == 13
        assert edition == "Standard"
        assert product_version == "13.0.5026.0"

    def test_parse_version_enterprise(self):
        """Test version parsing for Enterprise edition."""
        connector = SQLServerConnector()
        version_str = "Microsoft SQL Server 2022 - 16.0.1000.6 (X64)   Oct 20 2022   Enterprise Edition (64-bit)"

        major, edition, product_version = connector._parse_version(version_str)

        assert major == 16
        assert edition == "Enterprise"

    def test_parse_version_express(self):
        """Test version parsing for Express edition."""
        connector = SQLServerConnector()
        version_str = "Microsoft SQL Server 2019 - 15.0.2000.5 (X64)   Express Edition (64-bit)"

        major, edition, product_version = connector._parse_version(version_str)

        assert edition == "Express"

    def test_categorize_error_auth_failed(self):
        """Test error categorization for auth failure."""
        connector = SQLServerConnector()

        # Mock pyodbc error
        mock_error = Mock()
        mock_error.__str__ = Mock(return_value="Login failed for user 'sa' (18456)")

        msg, code = connector._categorize_error(mock_error)

        assert code == "AUTH_FAILED"
        assert "Authentication failed" in msg

    def test_categorize_error_connection_failed(self):
        """Test error categorization for connection failure."""
        connector = SQLServerConnector()

        mock_error = Mock()
        mock_error.__str__ = Mock(return_value="TCP Provider: No connection could be made")

        msg, code = connector._categorize_error(mock_error)

        assert code == "CONNECTION_FAILED"
        assert "Cannot connect" in msg

    def test_categorize_error_timeout(self):
        """Test error categorization for timeout."""
        connector = SQLServerConnector()

        mock_error = Mock()
        mock_error.__str__ = Mock(return_value="Timeout expired while attempting to connect")

        msg, code = connector._categorize_error(mock_error)

        assert code == "TIMEOUT"
        assert "timed out" in msg

    def test_categorize_error_driver_not_found(self):
        """Test error categorization for driver not found."""
        connector = SQLServerConnector()

        mock_error = Mock()
        mock_error.__str__ = Mock(return_value="Data source name not found and no default driver specified")

        msg, code = connector._categorize_error(mock_error)

        assert code == "DRIVER_NOT_FOUND"
        assert "ODBC driver" in msg


@pytest.mark.skipif(not PYODBC_AVAILABLE, reason="pyodbc not installed")
class TestSQLServerConnectorIntegration:
    """Integration tests requiring pyodbc (mocked)."""

    @pytest.fixture
    def mock_app(self):
        """Create mock Flask app context."""
        app = Mock()
        app.config = {'SQLSERVER_DRIVER': 'ODBC Driver 18 for SQL Server'}
        return app

    def test_test_connection_success(self, mock_app):
        """Test successful connection."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        # Mock version query
        mock_cursor.fetchone.side_effect = [
            ("Microsoft SQL Server 2019 - 15.0.4261.1 Developer Edition",),
            (1,)  # VIEW SERVER STATE permission
        ]

        with patch('app.connectors.sqlserver.current_app', mock_app):
            with patch('app.connectors.sqlserver.pyodbc') as mock_pyodbc:
                mock_pyodbc.connect.return_value = mock_conn

                connector = SQLServerConnector()
                result = connector.test_connection(
                    hostname='localhost',
                    port=1433,
                    auth_type='sql',
                    username='sa',
                    password='test123'
                )

        assert result.success is True
        assert result.edition == "Developer"
        assert result.has_view_server_state is True
        assert result.is_supported_version is True

    def test_test_connection_auth_failure(self, mock_app):
        """Test connection with auth failure."""
        import pyodbc

        with patch('app.connectors.sqlserver.current_app', mock_app):
            with patch('app.connectors.sqlserver.pyodbc') as mock_pyodbc:
                mock_pyodbc.Error = pyodbc.Error
                mock_pyodbc.connect.side_effect = pyodbc.Error(
                    "28000",
                    "[28000] Login failed for user 'sa' (18456)"
                )

                connector = SQLServerConnector()
                result = connector.test_connection(
                    hostname='localhost',
                    port=1433,
                    auth_type='sql',
                    username='sa',
                    password='wrong'
                )

        assert result.success is False
        assert result.error_code == "AUTH_FAILED"

    def test_test_connection_old_version(self, mock_app):
        """Test connection to unsupported SQL Server version."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        # Mock old version (SQL Server 2014 = version 12)
        mock_cursor.fetchone.side_effect = [
            ("Microsoft SQL Server 2014 - 12.0.5000.0 Standard Edition",),
            (1,)
        ]

        with patch('app.connectors.sqlserver.current_app', mock_app):
            with patch('app.connectors.sqlserver.pyodbc') as mock_pyodbc:
                mock_pyodbc.connect.return_value = mock_conn

                connector = SQLServerConnector()
                result = connector.test_connection(
                    hostname='localhost',
                    port=1433,
                    auth_type='sql',
                    username='sa',
                    password='test123'
                )

        assert result.success is True
        assert result.is_supported_version is False

    def test_test_connection_no_view_server_state(self, mock_app):
        """Test connection without VIEW SERVER STATE permission."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchone.side_effect = [
            ("Microsoft SQL Server 2019 - 15.0.4261.1 Developer Edition",),
            (0,)  # No permission
        ]

        with patch('app.connectors.sqlserver.current_app', mock_app):
            with patch('app.connectors.sqlserver.pyodbc') as mock_pyodbc:
                mock_pyodbc.connect.return_value = mock_conn

                connector = SQLServerConnector()
                result = connector.test_connection(
                    hostname='localhost',
                    port=1433,
                    auth_type='sql',
                    username='sa',
                    password='test123'
                )

        assert result.success is True
        assert result.has_view_server_state is False
