from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class AnimalModel(Base):

    __tablename__ = "animals"


    animal_id: Mapped[str] = mapped_column(
        String,
        primary_key=True
    )


    animal_type: Mapped[str] = mapped_column(
        String,
        nullable=False
    )


    status: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    lifecycle_status: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    ear_tag: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    rfid: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    dam_id: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    sire_id: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )
