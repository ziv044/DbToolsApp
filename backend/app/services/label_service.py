"""Service layer for label business logic."""
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from app.repositories.label_repository import LabelRepository
from app.repositories.server_repository import ServerRepository
from app.models.tenant import Label


class LabelService:
    """Service for label operations."""

    def __init__(self, session: Session):
        """Initialize with database session."""
        self.session = session
        self.label_repo = LabelRepository(session)
        self.server_repo = ServerRepository(session)

    def get_all_labels(self) -> Dict[str, Any]:
        """Get all labels with usage counts."""
        labels = self.label_repo.get_all()
        return {
            'labels': [
                {
                    **label.to_dict(),
                    'usage_count': self.label_repo.get_usage_count(label)
                }
                for label in labels
            ],
            'total': len(labels)
        }

    def get_label_by_id(self, label_id: UUID) -> Optional[Label]:
        """Get a label by ID."""
        return self.label_repo.get_by_id(label_id)

    def create_label(self, name: str, color: Optional[str] = None) -> Label:
        """Create a new label."""
        # Check if label already exists
        existing = self.label_repo.get_by_name(name)
        if existing:
            raise ValueError(f"Label '{name}' already exists")

        label = self.label_repo.create(name, color)
        self.session.commit()
        return label

    def update_label(self, label_id: UUID, name: Optional[str] = None, color: Optional[str] = None) -> Label:
        """Update a label."""
        label = self.label_repo.get_by_id(label_id)
        if not label:
            raise ValueError("Label not found")

        if name and name.lower().strip() != label.name:
            existing = self.label_repo.get_by_name(name)
            if existing:
                raise ValueError(f"Label '{name}' already exists")

        label = self.label_repo.update(label, name, color)
        self.session.commit()
        return label

    def delete_label(self, label_id: UUID) -> None:
        """Delete a label."""
        label = self.label_repo.get_by_id(label_id)
        if not label:
            raise ValueError("Label not found")

        self.label_repo.delete(label)
        self.session.commit()

    def assign_labels_to_server(self, server_id: UUID, label_names: List[str]) -> List[Label]:
        """Assign labels to a server, creating labels if they don't exist."""
        server = self.server_repo.get_by_id(server_id)
        if not server:
            raise ValueError("Server not found")

        labels = self.label_repo.assign_to_server(server, label_names)
        self.session.commit()
        return labels

    def remove_label_from_server(self, server_id: UUID, label_id: UUID) -> None:
        """Remove a label from a server."""
        server = self.server_repo.get_by_id(server_id)
        if not server:
            raise ValueError("Server not found")

        label = self.label_repo.get_by_id(label_id)
        if not label:
            raise ValueError("Label not found")

        self.label_repo.remove_from_server(server, label)
        self.session.commit()

    def get_server_labels(self, server_id: UUID) -> List[Label]:
        """Get all labels for a server."""
        return self.label_repo.get_labels_for_server(server_id)
