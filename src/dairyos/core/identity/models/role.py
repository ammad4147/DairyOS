"""
DairyOS Identity Role Model

CORE-003
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from ...database.base import Base


class Role(Base):

    __tablename__ = "identity_roles"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True
    )

    description: Mapped[str] = mapped_column(
        String(255)
    )