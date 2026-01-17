"""Repository for label data access operations."""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.tenant import Label, Server, server_labels


class LabelRepository:
    """Repository for label CRUD operations."""

    def __init__(self, session: Session):
        """Initialize with database session."""
        self.session = session

    def get_all(self) -> List[Label]:
        """Get all labels."""
        return self.session.query(Label).order_by(Label.name).all()

    def get_by_id(self, label_id: UUID) -> Optional[Label]:
        """Get a label by ID."""
        return self.session.query(Label).filter(Label.id == label_id).first()

    def get_by_name(self, name: str) -> Optional[Label]:
        """Get a label by name (case-insensitive)."""
        return self.session.query(Label).filter(
            Label.name == name.lower().strip()
        ).first()

    def create(self, name: str, color: Optional[str] = None) -> Label:
        """Create a new label."""
        label = Label(
            name=name.lower().strip(),
            color=color or '#6B7280'
        )
        self.session.add(label)
        self.session.flush()
        return label

    def update(self, label: Label, name: Optional[str] = None, color: Optional[str] = None) -> Label:
        """Update a label."""
        if name is not None:
            label.name = name.lower().strip()
        if color is not None:
            label.color = color
        self.session.flush()
        return label

    def delete(self, label: Label) -> None:
        """Delete a label."""
        self.session.delete(label)
        self.session.flush()

    def get_or_create(self, name: str, color: Optional[str] = None) -> Label:
        """Get a label by name or create it if it doesn't exist."""
        label = self.get_by_name(name)
        if not label:
            label = self.create(name, color)
        return label

    def assign_to_server(self, server: Server, label_names: List[str]) -> List[Label]:
        """Assign labels to a server, creating labels if they don't exist."""
        labels = []
        for name in label_names:
            if name and name.strip():
                label = self.get_or_create(name.strip())
                if label not in server.labels:
                    server.labels.append(label)
                labels.append(label)
        self.session.flush()
        return labels

    def remove_from_server(self, server: Server, label: Label) -> None:
        """Remove a label from a server."""
        if label in server.labels:
            server.labels.remove(label)
            self.session.flush()

    def get_labels_for_server(self, server_id: UUID) -> List[Label]:
        """Get all labels for a specific server."""
        server = self.session.query(Server).filter(Server.id == server_id).first()
        if server:
            return list(server.labels)
        return []

    def get_usage_count(self, label: Label) -> int:
        """Get the number of servers using this label."""
        return len([s for s in label.servers if not s.is_deleted])
