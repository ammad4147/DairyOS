"""Persisted daily milk-quality sample.

Quality is a bulk/daily milk characteristic and is deliberately separate
from the individual-animal production ledger. One recorded sample per
operational date is supported; updating the same date is an idempotent edit.
"""

from sqlalchemy import Column, DateTime, Float, Index, Integer, String, func

from ..database.base import Base
from dairyos.core.time_utils import utcnow


class MilkQualitySample(Base):
    __tablename__ = "milk_quality_samples"

    id = Column(Integer, primary_key=True, autoincrement=True)
    quality_date = Column(DateTime, nullable=False, index=True)
    fat_pct = Column(Float, nullable=False)
    snf_pct = Column(Float, nullable=False)
    sample_type = Column(String, nullable=False, default="BULK_TANK")
    notes = Column(String, nullable=True)
    recorded_by = Column(String, nullable=False, default="UI Operator")
    status = Column(String, nullable=False, default="RECORDED")
    recorded_at = Column(DateTime, nullable=False, default=utcnow)
    updated_at = Column(DateTime, nullable=False, default=utcnow)

    __table_args__ = (
        Index(
            "uq_milk_quality_sample_day",
            func.date(quality_date),
            unique=True,
            postgresql_where=(status == "RECORDED"),
            sqlite_where=(status == "RECORDED"),
        ),
    )
