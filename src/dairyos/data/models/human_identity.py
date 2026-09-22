from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from dairyos.core.time_utils import utcnow
from ..database.base import Base


class HumanIdentity(Base):
    """Named farm person used by the controlled desktop access layer."""

    __tablename__ = "human_identities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    display_name = Column(String, nullable=False)
    entry_group = Column(String, nullable=False)
    role = Column(String, nullable=False)
    permissions_json = Column(Text, nullable=True)
    pin_hash = Column(String, nullable=True)
    pin_salt = Column(String, nullable=True)
    pin_setup_hash = Column(String, nullable=True)
    failed_pin_attempts = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime, nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)
    updated_at = Column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)


class HumanSession(Base):
    """Short-lived authenticated human session; never stores a PIN."""

    __tablename__ = "human_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_hash = Column(String, nullable=False, unique=True, index=True)
    identity_id = Column(Integer, nullable=False, index=True)
    role = Column(String, nullable=False)
    entry_group = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=utcnow)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
