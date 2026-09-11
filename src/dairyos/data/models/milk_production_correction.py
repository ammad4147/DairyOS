"""Immutable audit records for authoritative Milk corrections."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String

from ..database.base import Base
from dairyos.core.time_utils import utcnow


class MilkProductionCorrection(Base):
    """Before/after record for every governed Milk update or void.

    The application exposes insertion only. The authoritative production row
    may change through the governed correction endpoints, while this table
    retains the original values, the resulting values, the reason and the
    operator who made the change.
    """

    __tablename__ = "milk_production_corrections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    production_id = Column(
        Integer,
        ForeignKey("milk_production.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    action = Column(String, nullable=False)
    reason = Column(String, nullable=False)
    operator = Column(String, nullable=False)
    before_json = Column(JSON, nullable=False)
    after_json = Column(JSON, nullable=False)
    source_request_id = Column(String, nullable=True, index=True)
    corrected_at = Column(DateTime, default=utcnow, nullable=False)
