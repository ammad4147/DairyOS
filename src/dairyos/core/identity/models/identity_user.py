"""
DairyOS Identity User Model

CORE-003
"""

from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from ...database.base import Base


class IdentityUser(Base):

    __tablename__ = "identity_users"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    username: Mapped[str] = mapped_column(
        String(100),
        unique=True
    )

    password_hash: Mapped[str] = mapped_column(
        String(255)
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )