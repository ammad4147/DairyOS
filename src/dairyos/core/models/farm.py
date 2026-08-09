"""
DairyOS Farm Entity
"""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from dairyos.data.database.base import Base


class Farm(Base):

    __tablename__ = "farms"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
    )

    location: Mapped[str] = mapped_column(
        String(100),
    )
