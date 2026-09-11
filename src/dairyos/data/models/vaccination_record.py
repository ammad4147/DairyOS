"""Relational authority for administered vaccination facts."""

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text

from dairyos.core.time_utils import utcnow
from dairyos.data.database.base import Base


class VaccinationRecord(Base):
    """One immutable administered-vaccination fact and its schedule state."""

    __tablename__ = "vaccinations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    animal_id = Column(
        String,
        ForeignKey("animal.animal_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    vaccine = Column(String, nullable=False, index=True)
    dose = Column(String, nullable=True)
    administered_date = Column(Date, nullable=False, index=True)
    next_due_date = Column(Date, nullable=True, index=True)
    schedule_status = Column(String, nullable=False, default="UNKNOWN_NEXT_DUE")
    batch_number = Column(String, nullable=True)
    veterinarian = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    operator = Column(String, nullable=False, default="API")
    status = Column(String, nullable=False, default="COMPLETED", index=True)
    source_event_id = Column(String, nullable=True, unique=True, index=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)
