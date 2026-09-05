"""Official static monthly Cost of Milk Production (COML) record.

A COML record is a management-confirmed monthly operating figure. It is
intentionally independent from transactional Finance, Milk, Feed Inventory,
and live production metrics.
"""

from sqlalchemy import Column, Date, DateTime, Integer, Numeric, String

from dairyos.core.time_utils import utcnow

from ..database.base import Base


class COMLRecord(Base):
    __tablename__ = "coml_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    month_start = Column(Date, nullable=False, unique=True, index=True)
    feed_cost_per_liter = Column(Numeric(18, 6), nullable=False)
    opex_cost_per_liter = Column(Numeric(18, 6), nullable=False)
    total_coml_per_liter = Column(Numeric(18, 6), nullable=False)
    status = Column(String, nullable=False, default="OFFICIAL")
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)
    updated_at = Column(DateTime, nullable=False, default=utcnow)
    locked_at = Column(DateTime, nullable=False, default=utcnow)
    updated_by = Column(String, nullable=False, default="UI Operator")
