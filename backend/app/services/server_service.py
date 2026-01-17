"""Service for Server business logic."""
from typing import Optional
from uuid import UUID
from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.models.tenant import Server
from app.repositories.server_repository import ServerRepository
from app.core.encryption import encrypt_password


class ServerValidationError(Exception):
    """Raised when server validation fails."""
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message)
        self.field = field
        self.message = message


class ServerNotFoundError(Exception):
    """Raised when server is not found."""
    pass


@dataclass
class CreateServerInput:
    """Input for creating a server."""
    name: str
    hostname: str
    port: int = 1433
    instance_name: Optional[str] = None
    auth_type: str = 'sql'
    username: Optional[str] = None
    password: Optional[str] = None


@dataclass
class UpdateServerInput:
    """Input for updating a server."""
    name: Optional[str] = None
    hostname: Optional[str] = None
    port: Optional[int] = None
    instance_name: Optional[str] = None
    auth_type: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


class ServerService:
    """Service for server management operations."""

    def __init__(self, session: Session):
        self.session = session
        self.repository = ServerRepository(session)

    def get_all(self) -> list[Server]:
        """Get all active servers."""
        return self.repository.get_all()

    def get_by_id(self, server_id: UUID) -> Server:
        """Get server by ID."""
        server = self.repository.get_by_id(server_id)
        if not server:
            raise ServerNotFoundError(f"Server with id {server_id} not found")
        return server

    def create(self, input: CreateServerInput) -> Server:
        """Create a new server."""
        self._validate_create(input)

        server = Server(
            name=input.name.strip(),
            hostname=input.hostname.strip(),
            port=input.port,
            instance_name=input.instance_name.strip() if input.instance_name else None,
            auth_type=input.auth_type,
            username=input.username.strip() if input.username else None,
            encrypted_password=encrypt_password(input.password) if input.password else None,
        )

        return self.repository.create(server)

    def update(self, server_id: UUID, input: UpdateServerInput) -> Server:
        """Update an existing server."""
        server = self.get_by_id(server_id)
        self._validate_update(input, server)

        if input.name is not None:
            server.name = input.name.strip()
        if input.hostname is not None:
            server.hostname = input.hostname.strip()
        if input.port is not None:
            server.port = input.port
        if input.instance_name is not None:
            server.instance_name = input.instance_name.strip() if input.instance_name else None
        if input.auth_type is not None:
            server.auth_type = input.auth_type
        if input.username is not None:
            server.username = input.username.strip() if input.username else None
        if input.password is not None:
            server.encrypted_password = encrypt_password(input.password) if input.password else None

        return self.repository.update(server)

    def delete(self, server_id: UUID) -> None:
        """Soft delete a server."""
        server = self.get_by_id(server_id)
        self.repository.soft_delete(server)

    def _validate_create(self, input: CreateServerInput) -> None:
        """Validate input for creating a server."""
        if not input.name or not input.name.strip():
            raise ServerValidationError("Name is required", "name")

        if not input.hostname or not input.hostname.strip():
            raise ServerValidationError("Hostname is required", "hostname")

        if not input.auth_type:
            raise ServerValidationError("Auth type is required", "auth_type")

        if input.auth_type not in Server.VALID_AUTH_TYPES:
            raise ServerValidationError(
                f"Invalid auth type. Must be one of: {', '.join(Server.VALID_AUTH_TYPES)}",
                "auth_type"
            )

        if input.auth_type == Server.AUTH_TYPE_SQL:
            if not input.username or not input.username.strip():
                raise ServerValidationError("Username is required for SQL authentication", "username")

        if self.repository.name_exists(input.name.strip()):
            raise ServerValidationError("Server with this name already exists", "name")

    def _validate_update(self, input: UpdateServerInput, server: Server) -> None:
        """Validate input for updating a server."""
        if input.name is not None:
            if not input.name.strip():
                raise ServerValidationError("Name cannot be empty", "name")
            if self.repository.name_exists(input.name.strip(), exclude_id=server.id):
                raise ServerValidationError("Server with this name already exists", "name")

        if input.hostname is not None and not input.hostname.strip():
            raise ServerValidationError("Hostname cannot be empty", "hostname")

        if input.auth_type is not None:
            if input.auth_type not in Server.VALID_AUTH_TYPES:
                raise ServerValidationError(
                    f"Invalid auth type. Must be one of: {', '.join(Server.VALID_AUTH_TYPES)}",
                    "auth_type"
                )

            # Check username requirement for SQL auth
            auth_type = input.auth_type
            username = input.username if input.username is not None else server.username
            if auth_type == Server.AUTH_TYPE_SQL and not username:
                raise ServerValidationError("Username is required for SQL authentication", "username")
