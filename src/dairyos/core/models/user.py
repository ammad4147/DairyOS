"""
DairyOS User Entity
"""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from dairyos.data.database.base import Base


class User(Base):

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    username: Mapped[str] = mapped_column(
        String(100),
    )

    full_name: Mapped[str] = mapped_column(
        String(100),
    )
