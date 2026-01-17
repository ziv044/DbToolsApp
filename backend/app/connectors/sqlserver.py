"""SQL Server connection handler."""
import re
from dataclasses import dataclass, field
from typing import Optional
from flask import current_app

from app.connectors.scripts import (
    DEPLOYMENT_VERSION,
    DEPLOYMENT_SCRIPTS,
    CHECK_PERMISSIONS,
)

try:
    import pyodbc
    PYODBC_AVAILABLE = True
except ImportError:
    PYODBC_AVAILABLE = False


class SQLServerConnectionError(Exception):
    """Raised when SQL Server connection fails."""
    pass


@dataclass
class ConnectionTestResult:
    """Result of a SQL Server connection test."""
    success: bool
    version: Optional[str] = None
    edition: Optional[str] = None
    product_version: Optional[str] = None
    has_view_server_state: bool = False
    is_supported_version: bool = False
    error: Optional[str] = None
    error_code: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        result = {
            'success': self.success,
        }
        if self.success:
            result.update({
                'version': self.version,
                'edition': self.edition,
                'product_version': self.product_version,
                'has_view_server_state': self.has_view_server_state,
                'is_supported_version': self.is_supported_version,
            })
        else:
            result.update({
                'error': self.error,
                'error_code': self.error_code,
            })
        return result


class DeploymentStatus:
    """Deployment status constants."""
    NOT_DEPLOYED = 'not_deployed'
    DEPLOYED = 'deployed'
    OUTDATED = 'outdated'
    FAILED = 'failed'


@dataclass
class PermissionCheckResult:
    """Result of permission check."""
    can_deploy: bool
    can_create_procedure: bool = False
    can_create_table: bool = False
    can_create_schema: bool = False
    can_view_server_state: bool = False
    missing_permissions: list = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'can_deploy': self.can_deploy,
            'can_create_procedure': self.can_create_procedure,
            'can_create_table': self.can_create_table,
            'can_create_schema': self.can_create_schema,
            'can_view_server_state': self.can_view_server_state,
            'missing_permissions': self.missing_permissions,
        }


@dataclass
class DeploymentResult:
    """Result of deployment operation."""
    success: bool
    version: Optional[str] = None
    deployed_at: Optional[str] = None
    error: Optional[str] = None
    error_step: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        result = {'success': self.success}
        if self.success:
            result.update({
                'version': self.version,
                'deployed_at': self.deployed_at,
            })
        else:
            result.update({
                'error': self.error,
                'error_step': self.error_step,
            })
        return result


@dataclass
class DeploymentStatusResult:
    """Result of deployment status check."""
    status: str
    version: Optional[str] = None
    deployed_at: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        result = {'status': self.status}
        if self.version:
            result['version'] = self.version
        if self.deployed_at:
            result['deployed_at'] = self.deployed_at
        if self.error:
            result['error'] = self.error
        return result


class SQLServerConnector:
    """Connector for SQL Server instances."""

    # Minimum supported SQL Server version (2016 = version 13)
    MIN_SUPPORTED_VERSION = 13

    # Connection timeout in seconds
    CONNECTION_TIMEOUT = 10

    # Default ODBC driver
    DEFAULT_DRIVER = 'ODBC Driver 18 for SQL Server'

    def __init__(self, driver: str = None):
        if not PYODBC_AVAILABLE:
            raise SQLServerConnectionError("pyodbc is not installed")
        # Store driver at init time to avoid needing Flask app context later
        if driver:
            self._driver = driver
        else:
            try:
                self._driver = current_app.config.get('SQLSERVER_DRIVER', self.DEFAULT_DRIVER)
            except RuntimeError:
                # Not in Flask app context, use default
                self._driver = self.DEFAULT_DRIVER

    def _get_driver(self) -> str:
        """Get the ODBC driver name."""
        return self._driver

    def _build_connection_string(
        self,
        hostname: str,
        port: int = 1433,
        instance_name: Optional[str] = None,
        auth_type: str = 'sql',
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: str = 'master'
    ) -> str:
        """
        Build ODBC connection string for SQL Server.

        Args:
            hostname: Server hostname or IP address
            port: TCP port (default 1433)
            instance_name: Named instance (optional)
            auth_type: 'sql' or 'windows'
            username: SQL Server username (for sql auth)
            password: SQL Server password (for sql auth)
            database: Database to connect to (default master)

        Returns:
            ODBC connection string
        """
        driver = self._get_driver()

        # Build server string
        if instance_name:
            server = f"{hostname}\\{instance_name}"
        else:
            server = f"{hostname},{port}"

        # Start connection string
        conn_str = f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};"

        # Add authentication
        if auth_type == 'windows':
            conn_str += "Trusted_Connection=yes;"
        else:
            if not username:
                raise SQLServerConnectionError("Username required for SQL authentication")
            conn_str += f"UID={username};PWD={password or ''};"

        # Trust server certificate (required for newer drivers)
        conn_str += "TrustServerCertificate=yes;"

        return conn_str

    def _parse_version(self, version_string: str) -> tuple[int, str, str]:
        """
        Parse SQL Server version string.

        Returns:
            Tuple of (major_version, edition, full_version)
        """
        # Extract version number (e.g., "16.0.1000.6")
        version_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', version_string)
        product_version = version_match.group(1) if version_match else 'Unknown'

        # Extract major version
        major_version = int(product_version.split('.')[0]) if version_match else 0

        # Extract edition
        edition = 'Unknown'
        if 'Enterprise' in version_string:
            edition = 'Enterprise'
        elif 'Standard' in version_string:
            edition = 'Standard'
        elif 'Developer' in version_string:
            edition = 'Developer'
        elif 'Express' in version_string:
            edition = 'Express'
        elif 'Web' in version_string:
            edition = 'Web'

        return major_version, edition, product_version

    def _categorize_error(self, error: pyodbc.Error) -> tuple[str, str]:
        """
        Categorize pyodbc error into user-friendly message and code.

        Returns:
            Tuple of (error_message, error_code)
        """
        error_str = str(error)

        # Login failed
        if 'Login failed' in error_str or '18456' in error_str:
            return "Authentication failed. Please check username and password.", "AUTH_FAILED"

        # Network errors
        if 'TCP Provider' in error_str or 'Named Pipes Provider' in error_str:
            return "Cannot connect to server. Please check hostname and port.", "CONNECTION_FAILED"

        # Timeout
        if 'timeout' in error_str.lower() or 'Timeout expired' in error_str:
            return "Connection timed out. Server may be unavailable or blocked by firewall.", "TIMEOUT"

        # Driver not found
        if 'Data source name not found' in error_str or 'driver' in error_str.lower():
            return "ODBC driver not found. Please install SQL Server ODBC driver.", "DRIVER_NOT_FOUND"

        # Server not found
        if 'server was not found' in error_str or 'could not be found' in error_str:
            return "Server not found. Please check hostname.", "SERVER_NOT_FOUND"

        # SSL/Certificate errors
        if 'SSL' in error_str or 'certificate' in error_str.lower():
            return "SSL/TLS connection error. Certificate validation failed.", "SSL_ERROR"

        # Default
        return f"Connection failed: {error_str}", "UNKNOWN_ERROR"

    def test_connection(
        self,
        hostname: str,
        port: int = 1433,
        instance_name: Optional[str] = None,
        auth_type: str = 'sql',
        username: Optional[str] = None,
        password: Optional[str] = None
    ) -> ConnectionTestResult:
        """
        Test connection to SQL Server and gather instance information.

        Args:
            hostname: Server hostname or IP address
            port: TCP port (default 1433)
            instance_name: Named instance (optional)
            auth_type: 'sql' or 'windows'
            username: SQL Server username (for sql auth)
            password: SQL Server password (for sql auth)

        Returns:
            ConnectionTestResult with success/failure and details
        """
        try:
            # Build connection string
            conn_str = self._build_connection_string(
                hostname=hostname,
                port=port,
                instance_name=instance_name,
                auth_type=auth_type,
                username=username,
                password=password,
                database='master'
            )

            # Attempt connection with timeout
            conn = pyodbc.connect(conn_str, timeout=self.CONNECTION_TIMEOUT)
            cursor = conn.cursor()

            # Get version information
            cursor.execute("SELECT @@VERSION")
            version_string = cursor.fetchone()[0]

            major_version, edition, product_version = self._parse_version(version_string)

            # Check for VIEW SERVER STATE permission
            cursor.execute("SELECT HAS_PERMS_BY_NAME(NULL, NULL, 'VIEW SERVER STATE')")
            has_view_server_state = cursor.fetchone()[0] == 1

            # Check if version is supported
            is_supported = major_version >= self.MIN_SUPPORTED_VERSION

            conn.close()

            return ConnectionTestResult(
                success=True,
                version=version_string,
                edition=edition,
                product_version=product_version,
                has_view_server_state=has_view_server_state,
                is_supported_version=is_supported,
            )

        except pyodbc.Error as e:
            error_msg, error_code = self._categorize_error(e)
            return ConnectionTestResult(
                success=False,
                error=error_msg,
                error_code=error_code,
            )
        except SQLServerConnectionError as e:
            return ConnectionTestResult(
                success=False,
                error=str(e),
                error_code='CONFIG_ERROR',
            )
        except Exception as e:
            return ConnectionTestResult(
                success=False,
                error=f"Unexpected error: {str(e)}",
                error_code='UNEXPECTED_ERROR',
            )

    def connect(
        self,
        hostname: str,
        port: int = 1433,
        instance_name: Optional[str] = None,
        auth_type: str = 'sql',
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: str = 'master'
    ):
        """
        Create a connection to SQL Server.

        Returns:
            pyodbc.Connection object
        """
        conn_str = self._build_connection_string(
            hostname=hostname,
            port=port,
            instance_name=instance_name,
            auth_type=auth_type,
            username=username,
            password=password,
            database=database
        )
        return pyodbc.connect(conn_str, timeout=self.CONNECTION_TIMEOUT)

    def check_deployment_permissions(
        self,
        hostname: str,
        port: int = 1433,
        instance_name: Optional[str] = None,
        auth_type: str = 'sql',
        username: Optional[str] = None,
        password: Optional[str] = None
    ) -> PermissionCheckResult:
        """
        Check if user has required permissions to deploy monitoring objects.

        Returns:
            PermissionCheckResult with permission details
        """
        try:
            conn = self.connect(
                hostname=hostname,
                port=port,
                instance_name=instance_name,
                auth_type=auth_type,
                username=username,
                password=password,
                database='master'
            )
            cursor = conn.cursor()

            # Execute permission check query
            cursor.execute(CHECK_PERMISSIONS)
            row = cursor.fetchone()

            can_create_procedure = row[0] == 1
            can_create_table = row[1] == 1
            can_create_schema = row[2] == 1
            can_view_server_state = row[3] == 1

            conn.close()

            # Build list of missing permissions
            missing = []
            if not can_create_procedure:
                missing.append('CREATE PROCEDURE')
            if not can_create_table:
                missing.append('CREATE TABLE')
            if not can_create_schema:
                missing.append('CREATE SCHEMA')
            if not can_view_server_state:
                missing.append('VIEW SERVER STATE')

            # Can deploy if has all required permissions
            can_deploy = can_create_procedure and can_create_table and can_create_schema

            return PermissionCheckResult(
                can_deploy=can_deploy,
                can_create_procedure=can_create_procedure,
                can_create_table=can_create_table,
                can_create_schema=can_create_schema,
                can_view_server_state=can_view_server_state,
                missing_permissions=missing,
            )

        except Exception as e:
            return PermissionCheckResult(
                can_deploy=False,
                missing_permissions=[f'Error checking permissions: {str(e)}'],
            )

    def deploy_monitoring(
        self,
        hostname: str,
        port: int = 1433,
        instance_name: Optional[str] = None,
        auth_type: str = 'sql',
        username: Optional[str] = None,
        password: Optional[str] = None
    ) -> DeploymentResult:
        """
        Deploy monitoring objects to SQL Server.

        Deploys schema, config table, and stored procedures.
        Idempotent - safe to re-run.

        Returns:
            DeploymentResult with success/failure details
        """
        try:
            # First check permissions
            perm_check = self.check_deployment_permissions(
                hostname=hostname,
                port=port,
                instance_name=instance_name,
                auth_type=auth_type,
                username=username,
                password=password
            )

            if not perm_check.can_deploy:
                return DeploymentResult(
                    success=False,
                    error=f"Insufficient permissions: {', '.join(perm_check.missing_permissions)}",
                    error_step='permission_check',
                )

            # Connect and deploy
            conn = self.connect(
                hostname=hostname,
                port=port,
                instance_name=instance_name,
                auth_type=auth_type,
                username=username,
                password=password,
                database='master'
            )
            cursor = conn.cursor()

            # Execute each deployment script
            for step_name, script in DEPLOYMENT_SCRIPTS:
                try:
                    cursor.execute(script)
                    conn.commit()
                except pyodbc.Error as e:
                    conn.rollback()
                    conn.close()
                    return DeploymentResult(
                        success=False,
                        error=str(e),
                        error_step=step_name,
                    )

            # Get deployment timestamp
            cursor.execute("""
                SELECT [Value] FROM DbTools.Config WHERE [Key] = 'DeployedAt'
            """)
            row = cursor.fetchone()
            deployed_at = row[0] if row else None

            conn.close()

            return DeploymentResult(
                success=True,
                version=DEPLOYMENT_VERSION,
                deployed_at=deployed_at,
            )

        except pyodbc.Error as e:
            error_msg, _ = self._categorize_error(e)
            return DeploymentResult(
                success=False,
                error=error_msg,
                error_step='connection',
            )
        except Exception as e:
            return DeploymentResult(
                success=False,
                error=f"Unexpected error: {str(e)}",
                error_step='unknown',
            )

    def get_deployment_status(
        self,
        hostname: str,
        port: int = 1433,
        instance_name: Optional[str] = None,
        auth_type: str = 'sql',
        username: Optional[str] = None,
        password: Optional[str] = None
    ) -> DeploymentStatusResult:
        """
        Get current deployment status from SQL Server.

        Returns:
            DeploymentStatusResult with status details
        """
        try:
            conn = self.connect(
                hostname=hostname,
                port=port,
                instance_name=instance_name,
                auth_type=auth_type,
                username=username,
                password=password,
                database='master'
            )
            cursor = conn.cursor()

            # Check if schema exists
            cursor.execute("""
                SELECT 1 FROM sys.schemas WHERE name = 'DbTools'
            """)
            if not cursor.fetchone():
                conn.close()
                return DeploymentStatusResult(status=DeploymentStatus.NOT_DEPLOYED)

            # Check if config table exists
            cursor.execute("""
                SELECT 1 FROM sys.objects
                WHERE object_id = OBJECT_ID(N'DbTools.Config') AND type = 'U'
            """)
            if not cursor.fetchone():
                conn.close()
                return DeploymentStatusResult(status=DeploymentStatus.NOT_DEPLOYED)

            # Get version and deployed_at from config
            cursor.execute("""
                SELECT [Key], [Value] FROM DbTools.Config
                WHERE [Key] IN ('Version', 'DeployedAt')
            """)
            config = {row[0]: row[1] for row in cursor.fetchall()}

            conn.close()

            deployed_version = config.get('Version')
            deployed_at = config.get('DeployedAt')

            if not deployed_version:
                return DeploymentStatusResult(status=DeploymentStatus.NOT_DEPLOYED)

            # Check if deployed version matches current version
            if deployed_version != DEPLOYMENT_VERSION:
                return DeploymentStatusResult(
                    status=DeploymentStatus.OUTDATED,
                    version=deployed_version,
                    deployed_at=deployed_at,
                )

            return DeploymentStatusResult(
                status=DeploymentStatus.DEPLOYED,
                version=deployed_version,
                deployed_at=deployed_at,
            )

        except pyodbc.Error as e:
            error_msg, _ = self._categorize_error(e)
            return DeploymentStatusResult(
                status=DeploymentStatus.FAILED,
                error=error_msg,
            )
        except Exception as e:
            return DeploymentStatusResult(
                status=DeploymentStatus.FAILED,
                error=f"Unexpected error: {str(e)}",
            )
