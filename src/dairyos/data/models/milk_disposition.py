"""Persisted accounting destination for produced milk litres."""

from decimal import Decimal

from sqlalchemy import Column, Date, DateTime, Float, Index, Integer, Numeric, String

from dairyos.core.time_utils import utcnow

from ..database.base import Base


class MilkDisposition(Base):
    __tablename__ = "milk_dispositions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    production_date = Column(Date, nullable=False, index=True)
    disposition_type = Column(String, nullable=False)
    quantity_litres = Column(Float, nullable=False)

    sale_id = Column(String, nullable=True, index=True)
    counterparty = Column(String, nullable=True)
    selling_price_per_litre = Column(Numeric(18, 6), nullable=True)
    amount_due = Column(Numeric(18, 2), nullable=False, default=0)
    amount_received = Column(Numeric(18, 2), nullable=False, default=0)

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
    def receivable_outstanding(self) -> Decimal:
        return max(
            Decimal(self.amount_due or 0)
            - Decimal(self.amount_received or 0),
            Decimal("0.00"),
        )
