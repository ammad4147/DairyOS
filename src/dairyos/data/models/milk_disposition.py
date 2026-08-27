"""Persisted accounting destination for produced milk litres."""

from sqlalchemy import Column, Date, DateTime, Float, Index, Integer, String

from ..database.base import Base
from dairyos.core.time_utils import utcnow


class MilkDisposition(Base):
    __tablename__ = "milk_dispositions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    production_date = Column(Date, nullable=False, index=True)
    disposition_type = Column(String, nullable=False)
    quantity_litres = Column(Float, nullable=False)

    sale_id = Column(String, nullable=True, index=True)
    counterparty = Column(String, nullable=True)
    selling_price_per_litre = Column(Float, nullable=True)
    amount_due = Column(Float, nullable=False, default=0.0)
    amount_received = Column(Float, nullable=False, default=0.0)

    notes = Column(String, nullable=True)
    recorded_by = Column(String, nullable=True)
    status = Column(String, nullable=False, default="RECORDED")
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, nullable=False)

    __table_args__ = (
        Index("ix_milk_dispositions_date_type", "production_date", "disposition_type"),
        Index(
            "uq_milk_dispositions_sale_id",
            "sale_id",
            unique=True,
            postgresql_where=(sale_id.is_not(None)),
        ),
    )

    @property
    def receivable_outstanding(self) -> float:
        return max(
            float(self.amount_due or 0.0)
            - float(self.amount_received or 0.0),
            0.0,
        )
