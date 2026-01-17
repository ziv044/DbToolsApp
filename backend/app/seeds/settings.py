"""Seed data for tenant settings."""
from sqlalchemy.orm import Session

from app.models.tenant import Setting


def seed_default_settings(session: Session) -> int:
    """
    Seed the settings table with default settings.

    Args:
        session: SQLAlchemy session for the tenant database

    Returns:
        Number of settings created
    """
    created_count = 0
    defaults = Setting.get_default_settings()

    for key, value in defaults.items():
        # Check if setting already exists
        existing = session.query(Setting).filter_by(key=key).first()
        if not existing:
            setting = Setting(key=key, value=value)
            session.add(setting)
            created_count += 1

    if created_count > 0:
        session.commit()

    return created_count


def get_setting(session: Session, key: str, default=None):
    """Get a setting value by key."""
    setting = session.query(Setting).filter_by(key=key).first()
    if setting:
        return setting.value
    return default


def set_setting(session: Session, key: str, value) -> Setting:
    """Set a setting value."""
    setting = session.query(Setting).filter_by(key=key).first()
    if setting:
        setting.value = value
    else:
        setting = Setting(key=key, value=value)
        session.add(setting)
    session.commit()
    return setting
