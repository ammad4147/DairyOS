from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime

from ..database.base import Base
from dairyos.core.time_utils import utcnow


class FeedRecord(Base):

    __tablename__ = "feed_record"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    animal_id = Column(
        String,
        nullable=True
    )

    group_or_pen = Column(
        String,
        nullable=True
    )

    feed_type = Column(
        String,
        nullable=False
    )

    quantity_kg = Column(
        Float,
        default=0.0,
        nullable=False
    )

    feeding_date = Column(
        DateTime,
        default=utcnow,
        nullable=False
    )

    notes = Column(
        String,
        nullable=True
    )

    status = Column(
        String,
        default="RECORDED"
    )
