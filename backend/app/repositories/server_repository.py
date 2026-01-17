"""Repository for Server model operations."""
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.tenant import Server
from app.repositories.base import BaseRepository


class ServerRepository(BaseRepository[Server]):
    """Repository for Server CRUD operations."""

    def __init__(self, session: Session):
        super().__init__(session, Server)

    def get_by_id(self, id: UUID, include_deleted: bool = False) -> Optional[Server]:
        """Get server by ID, optionally including deleted servers."""
        query = self.session.query(Server).filter(Server.id == id)
        if not include_deleted:
            query = query.filter(Server.is_deleted == False)  # noqa: E712
        return query.first()

    def get_by_name(self, name: str) -> Optional[Server]:
        """Get server by name (case-insensitive)."""
        return self.session.query(Server).filter(
            Server.name.ilike(name),
            Server.is_deleted == False  # noqa: E712
        ).first()

    def get_all(self, include_deleted: bool = False) -> list[Server]:
        """Get all servers, optionally including deleted ones."""
        query = self.session.query(Server)
        if not include_deleted:
            query = query.filter(Server.is_deleted == False)  # noqa: E712
        return query.order_by(Server.name).all()

    def soft_delete(self, server: Server) -> Server:
        """Soft delete a server by setting is_deleted flag."""
        server.is_deleted = True
        self.session.flush()
        return server

    def name_exists(self, name: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if server name already exists (excluding specified ID)."""
        query = self.session.query(Server).filter(
            Server.name.ilike(name),
            Server.is_deleted == False  # noqa: E712
        )
        if exclude_id:
            query = query.filter(Server.id != exclude_id)
        return query.first() is not None
