from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from ..base import Base


class OperationalEventModel(Base):

    __tablename__ = "operational_events"


    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )


    event_type: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )


    source: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )


    description: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )


    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )
