"""Service layer for server group operations."""
from dataclasses import dataclass
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.tenant import ServerGroup
from app.repositories.group_repository import GroupRepository


class GroupValidationError(Exception):
    """Raised when group validation fails."""
    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


class GroupNotFoundError(Exception):
    """Raised when group is not found."""
    pass


class ServerNotFoundError(Exception):
    """Raised when server is not found."""
    pass


@dataclass
class CreateGroupInput:
    """Input for creating a group."""
    name: str
    description: Optional[str] = None
    color: Optional[str] = None


@dataclass
class UpdateGroupInput:
    """Input for updating a group."""
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None


class GroupService:
    """Service for server group operations."""

    def __init__(self, session: Session):
        self.session = session
        self.repository = GroupRepository(session)

    def _validate_name(self, name: str, exclude_id: Optional[UUID] = None) -> None:
        """Validate group name."""
        if not name or not name.strip():
            raise GroupValidationError("Name is required", "name")
        if len(name) > 255:
            raise GroupValidationError("Name must be 255 characters or less", "name")
        if self.repository.name_exists(name.strip(), exclude_id):
            raise GroupValidationError("A group with this name already exists", "name")

    def _validate_color(self, color: Optional[str]) -> None:
        """Validate color format."""
        if color:
            if not color.startswith('#') or len(color) != 7:
                raise GroupValidationError("Color must be a valid hex color (e.g., #FF5733)", "color")

    def create(self, input: CreateGroupInput) -> ServerGroup:
        """Create a new server group."""
        self._validate_name(input.name)
        self._validate_color(input.color)

        group = ServerGroup(
            name=input.name.strip(),
            description=input.description.strip() if input.description else None,
            color=input.color
        )
        self.repository.create(group)
        return group

    def get_all(self) -> List[ServerGroup]:
        """Get all server groups."""
        return self.repository.get_all()

    def get_by_id(self, group_id: UUID) -> ServerGroup:
        """Get a group by ID."""
        group = self.repository.get_by_id(group_id)
        if not group:
            raise GroupNotFoundError()
        return group

    def update(self, group_id: UUID, input: UpdateGroupInput) -> ServerGroup:
        """Update a server group."""
        group = self.get_by_id(group_id)

        if input.name is not None:
            self._validate_name(input.name, exclude_id=group_id)
            group.name = input.name.strip()

        if input.description is not None:
            group.description = input.description.strip() if input.description else None

        if input.color is not None:
            self._validate_color(input.color)
            group.color = input.color if input.color else None

        return group

    def delete(self, group_id: UUID) -> None:
        """Delete a server group."""
        group = self.get_by_id(group_id)
        self.repository.delete(group)

    def add_servers(self, group_id: UUID, server_ids: List[UUID]) -> ServerGroup:
        """Add servers to a group."""
        group = self.get_by_id(group_id)

        for server_id in server_ids:
            server = self.repository.get_server(server_id)
            if not server:
                raise ServerNotFoundError(f"Server {server_id} not found")
            self.repository.add_server(group, server)

        return group

    def remove_server(self, group_id: UUID, server_id: UUID) -> ServerGroup:
        """Remove a server from a group."""
        group = self.get_by_id(group_id)

        server = self.repository.get_server(server_id)
        if not server:
            raise ServerNotFoundError(f"Server {server_id} not found")

        self.repository.remove_server(group, server)
        return group
