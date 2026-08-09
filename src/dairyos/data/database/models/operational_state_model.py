from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import JSON
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from ..base import Base


class OperationalStateModel(Base):
    """
    Database snapshot of current farm operational state.

    Stores the latest operational truth.

    Historical events remain in:
        operational_events

    This table stores projection state only.
    """


    __tablename__ = "operational_states"


    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )


    farm_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
        unique=True,
    )


    operational_date: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )


    state_payload: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )


    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )
