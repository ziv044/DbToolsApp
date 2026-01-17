"""Repository for ServerGroup operations."""
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.tenant import ServerGroup, Server
from app.repositories.base import BaseRepository


class GroupRepository(BaseRepository[ServerGroup]):
    """Repository for ServerGroup CRUD operations."""

    def __init__(self, session: Session):
        super().__init__(session, ServerGroup)

    def get_by_name(self, name: str) -> Optional[ServerGroup]:
        """Get group by name."""
        return self.session.query(ServerGroup).filter(
            ServerGroup.name == name
        ).first()

    def name_exists(self, name: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if group name already exists."""
        query = self.session.query(ServerGroup).filter(
            ServerGroup.name == name
        )
        if exclude_id:
            query = query.filter(ServerGroup.id != exclude_id)
        return query.first() is not None

    def add_server(self, group: ServerGroup, server: Server) -> None:
        """Add a server to a group."""
        if server not in group.servers:
            group.servers.append(server)

    def remove_server(self, group: ServerGroup, server: Server) -> None:
        """Remove a server from a group."""
        if server in group.servers:
            group.servers.remove(server)

    def get_server(self, server_id: UUID) -> Optional[Server]:
        """Get a server by ID (to add to group)."""
        return self.session.query(Server).filter(
            Server.id == server_id,
            Server.is_deleted == False
        ).first()
