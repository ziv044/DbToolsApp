"""Seed data for metric types."""
from sqlalchemy.orm import Session

from app.models.tenant import MetricType, METRIC_TYPES_SEED


def seed_metric_types(session: Session) -> int:
    """
    Seed the metric_types table with default metric types.

    Args:
        session: SQLAlchemy session for the tenant database

    Returns:
        Number of metric types created
    """
    created_count = 0

    for name, unit, description in METRIC_TYPES_SEED:
        # Check if metric type already exists
        existing = session.query(MetricType).filter_by(name=name).first()
        if not existing:
            metric_type = MetricType(
                name=name,
                unit=unit,
                description=description
            )
            session.add(metric_type)
            created_count += 1

    if created_count > 0:
        session.commit()

    return created_count


def get_metric_type_by_name(session: Session, name: str) -> MetricType | None:
    """Get a metric type by name."""
    return session.query(MetricType).filter_by(name=name).first()
