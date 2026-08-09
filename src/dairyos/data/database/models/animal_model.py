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
