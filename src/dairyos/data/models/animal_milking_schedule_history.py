from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime

from ..database.base import Base


class AnimalMilkingScheduleHistory(Base):
    """
    Tracks changes to an animal's milking frequency over time.

    Milking frequency (twice vs. thrice daily) is expected to change
    over an animal's lactation cycle, not just be a static setting.
    This table preserves the full history rather than silently
    overwriting the current value on Animal, so changes remain
    traceable — who changed it, when, and why.
    """

    __tablename__ = "animal_milking_schedule_history"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    animal_id = Column(
        String,
        ForeignKey("animal.animal_id"),
        nullable=False,
        index=True
    )

    milking_frequency = Column(
        String,
        nullable=False
    )

    effective_from = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # Null while this is the current/active record.
    effective_to = Column(
        DateTime,
        nullable=True
    )

    changed_by = Column(
        String,
        nullable=True
    )

    reason = Column(
        String,
        nullable=True
    )
