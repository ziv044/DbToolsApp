"""Deployment service for SQL Server monitoring objects."""
from uuid import UUID
from typing import Optional

from sqlalchemy.orm import Session

from app.connectors import (
    SQLServerConnector,
    DeploymentStatus,
    DeploymentResult,
    DeploymentStatusResult,
    PermissionCheckResult,
)
from app.connectors.sqlserver import PYODBC_AVAILABLE
from app.core.encryption import decrypt_password, EncryptionError
from app.models.tenant import Server


class DeploymentError(Exception):
    """Raised when deployment fails."""
    def __init__(self, message: str, code: str = 'DEPLOYMENT_ERROR'):
        self.message = message
        self.code = code
        super().__init__(message)


class DeploymentService:
    """Service for deploying monitoring objects to SQL Servers."""

    # Status constant for monitored servers
    STATUS_MONITORED = 'monitored'

    def __init__(self, session: Session):
        self.session = session

    def _get_server(self, server_id: UUID) -> Server:
        """Get server by ID, raise error if not found."""
        server = self.session.query(Server).filter(
            Server.id == server_id,
            Server.is_deleted == False
        ).first()

        if not server:
            raise DeploymentError(f'Server with id {server_id} not found', 'NOT_FOUND')

        return server

    def _get_decrypted_password(self, server: Server) -> Optional[str]:
        """Decrypt server password."""
        if not server.encrypted_password:
            return None

        try:
            return decrypt_password(server.encrypted_password)
        except EncryptionError as e:
            raise DeploymentError(f'Failed to decrypt password: {e}', 'DECRYPTION_ERROR')

    def _get_connection_params(self, server: Server) -> dict:
        """Build connection parameters for a server."""
        return {
            'hostname': server.hostname,
            'port': server.port,
            'instance_name': server.instance_name,
            'auth_type': server.auth_type,
            'username': server.username,
            'password': self._get_decrypted_password(server),
        }

    def check_permissions(self, server_id: UUID) -> PermissionCheckResult:
        """
        Check if server has required permissions for deployment.

        Args:
            server_id: ID of the server to check

        Returns:
            PermissionCheckResult with permission details
        """
        if not PYODBC_AVAILABLE:
            raise DeploymentError('SQL Server connectivity not available', 'DRIVER_NOT_INSTALLED')

        server = self._get_server(server_id)
        params = self._get_connection_params(server)

        connector = SQLServerConnector()
        return connector.check_deployment_permissions(**params)

    def deploy(self, server_id: UUID) -> DeploymentResult:
        """
        Deploy monitoring objects to SQL Server.

        Args:
            server_id: ID of the server to deploy to

        Returns:
            DeploymentResult with success/failure details
        """
        if not PYODBC_AVAILABLE:
            raise DeploymentError('SQL Server connectivity not available', 'DRIVER_NOT_INSTALLED')

        server = self._get_server(server_id)
        params = self._get_connection_params(server)

        connector = SQLServerConnector()
        result = connector.deploy_monitoring(**params)

        # Update server status on success
        if result.success:
            server.status = self.STATUS_MONITORED
            self.session.commit()

        return result

    def get_status(self, server_id: UUID) -> DeploymentStatusResult:
        """
        Get deployment status from SQL Server.

        Args:
            server_id: ID of the server to check

        Returns:
            DeploymentStatusResult with status details
        """
        if not PYODBC_AVAILABLE:
            raise DeploymentError('SQL Server connectivity not available', 'DRIVER_NOT_INSTALLED')

        server = self._get_server(server_id)
        params = self._get_connection_params(server)

        connector = SQLServerConnector()
        return connector.get_deployment_status(**params)
