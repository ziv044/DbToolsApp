"""Base repository class with common CRUD operations."""
from typing import TypeVar, Generic, Type, Optional
from uuid import UUID
from sqlalchemy.orm import Session

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """Base repository providing CRUD operations for a model."""

    def __init__(self, session: Session, model: Type[T]):
        self.session = session
        self.model = model

    def get_by_id(self, id: UUID) -> Optional[T]:
        """Get entity by ID."""
        return self.session.query(self.model).filter(
            self.model.id == id
        ).first()

    def get_all(self) -> list[T]:
        """Get all entities."""
        return self.session.query(self.model).all()

    def create(self, entity: T) -> T:
        """Create a new entity."""
        self.session.add(entity)
        self.session.flush()
        return entity

    def update(self, entity: T) -> T:
        """Update an existing entity."""
        self.session.merge(entity)
        self.session.flush()
        return entity

    def delete(self, entity: T) -> None:
        """Delete an entity."""
        self.session.delete(entity)
        self.session.flush()
