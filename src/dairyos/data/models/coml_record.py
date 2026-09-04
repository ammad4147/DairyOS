"""Official static monthly Cost of Production (COP) record.

A COP record is a management-confirmed monthly operating figure. It is
intentionally independent from transactional Finance, Milk, Feed Inventory,
and live production metrics. ``official_source`` records whether the operator
made the governed automatic calculation or a manual calculation official.
"""

from sqlalchemy import Column, Date, DateTime, Float, Integer, String

from ..database.base import Base
from dairyos.core.time_utils import utcnow


class COMLRecord(Base):
    __tablename__ = "coml_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    month_start = Column(Date, nullable=False, unique=True, index=True)
    feed_cost_per_liter = Column(Float, nullable=False)
    opex_cost_per_liter = Column(Float, nullable=False)
    total_coml_per_liter = Column(Float, nullable=False)
    status = Column(String, nullable=False, default="OFFICIAL")
    official_source = Column(String, nullable=False, default="UNSPECIFIED")
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)
    updated_at = Column(DateTime, nullable=False, default=utcnow)
    locked_at = Column(DateTime, nullable=False, default=utcnow)
    updated_by = Column(String, nullable=False, default="UI Operator")