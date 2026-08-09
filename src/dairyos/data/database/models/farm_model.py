from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class FarmModel(Base):

    __tablename__ = "farms"


    farm_id: Mapped[str] = mapped_column(
        String,
        primary_key=True
    )


    farm_name: Mapped[str] = mapped_column(
        String,
        nullable=False
    )


    location: Mapped[str] = mapped_column(
        String,
        nullable=False
    )
