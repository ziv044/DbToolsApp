import re
import uuid
from datetime import datetime, timezone

from sqlalchemy import event
from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db

# Slug validation: alphanumeric + hyphens, 3-50 chars, must start/end with alphanumeric
SLUG_PATTERN = re.compile(r'^[a-z0-9][a-z0-9-]{1,48}[a-z0-9]$')


def utc_now():
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


class Tenant(db.Model):
    """System-level tenant model stored in dbtools_system database."""

    __tablename__ = 'tenants'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default='active')
    settings = db.Column(db.JSON, nullable=False, default=dict)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now
    )

    __table_args__ = (
        db.CheckConstraint(
            "status IN ('active', 'suspended')",
            name='ck_tenants_status'
        ),
    )

    def __repr__(self):
        return f'<Tenant {self.slug}>'

    @staticmethod
    def validate_slug(slug: str) -> bool:
        """Validate slug format: alphanumeric + hyphens, 3-50 chars."""
        if not slug or len(slug) < 3 or len(slug) > 50:
            return False
        return bool(SLUG_PATTERN.match(slug.lower()))


@event.listens_for(Tenant, 'before_insert')
@event.listens_for(Tenant, 'before_update')
def validate_tenant_slug(mapper, connection, target):
    """Validate slug before insert/update."""
    if target.slug:
        target.slug = target.slug.lower()
        if not Tenant.validate_slug(target.slug):
            raise ValueError(
                f"Invalid slug format: '{target.slug}'. "
                "Must be 3-50 chars, alphanumeric + hyphens, "
                "start and end with alphanumeric."
            )
