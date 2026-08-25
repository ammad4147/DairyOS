from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from dairyos.core.time_utils import utcnow
from ..database.base import Base


class User(Base):
    """Persisted DairyOS user account with customizable access and email."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    password_salt = Column(String, nullable=False)
    role = Column(String, nullable=False)
    job_title = Column(String, nullable=True)
    personal_email = Column(String, nullable=True)
    permissions_json = Column(Text, nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)
