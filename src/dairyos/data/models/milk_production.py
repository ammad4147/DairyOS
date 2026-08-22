"""Persisted per-animal milk production record.

The three yield columns are nullable by design: NULL means no figure was
entered, while 0.0 means an operator explicitly recorded zero production.
"""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)

from ..database.base import Base
from dairyos.core.time_utils import utcnow


class MilkProduction(Base):
    __tablename__ = "milk_production"

    id = Column(Integer, primary_key=True, autoincrement=True)
    animal_id = Column(
        String,
        ForeignKey("animal.animal_id"),
        nullable=False,
        index=True,
    )
    production_date = Column(DateTime, default=utcnow, nullable=False)
    recorded_at = Column(DateTime, default=utcnow, nullable=False)
    milking_session = Column(String, nullable=True)
    session_ledger = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    morning_yield = Column(Float, nullable=True)
    afternoon_yield = Column(Float, nullable=True)
    evening_yield = Column(Float, nullable=True)
    total_yield = Column(Float, nullable=True)
    status = Column(String, default="RECORDED")
    notes = Column(String, nullable=True)

    __table_args__ = (
        Index(
            "uq_milk_production_ledger_animal_day",
            "animal_id",
            func.date(production_date),
            unique=True,
            postgresql_where=session_ledger,
            sqlite_where=session_ledger,
        ),
    )

    @property
    def entered_yields(self):
        return [
            value
            for value in (
                self.morning_yield,
                self.afternoon_yield,
                self.evening_yield,
            )
            if value is not None
        ]

    @property
    def has_entered_yield(self) -> bool:
        return bool(self.entered_yields)

    def calculate_total(self):
        entered = self.entered_yields
        self.total_yield = sum(entered) if entered else None
        return self.total_yield
