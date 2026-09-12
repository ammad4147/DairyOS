"""Persisted per-animal milk production record.

The three yield columns are nullable by design: NULL means no figure was
entered, while 0.0 means an operator explicitly recorded zero production.
"""

from math import isfinite

from sqlalchemy import (
    Boolean,
    CheckConstraint,
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


_MILK_FINITE_NONNEGATIVE = """
(
    (morning_yield IS NULL OR
        (morning_yield >= 0 AND
         morning_yield <= 1.7976931348623157e308))
    AND (afternoon_yield IS NULL OR
        (afternoon_yield >= 0 AND
         afternoon_yield <= 1.7976931348623157e308))
    AND (evening_yield IS NULL OR
        (evening_yield >= 0 AND
         evening_yield <= 1.7976931348623157e308))
    AND (total_yield IS NULL OR
        (total_yield >= 0 AND
         total_yield <= 1.7976931348623157e308))
)
"""

_MILK_GOVERNED_INTEGRITY = f"""
(
    (session_ledger = FALSE AND {_MILK_FINITE_NONNEGATIVE})
    OR (
        session_ledger = TRUE
        AND {_MILK_FINITE_NONNEGATIVE}
        AND (
            (
                morning_yield IS NULL
                AND afternoon_yield IS NULL
                AND evening_yield IS NULL
                AND total_yield IS NULL
            )
            OR (
                total_yield IS NOT NULL
                AND ABS(
                    total_yield - (
                        COALESCE(morning_yield, 0.0)
                        + COALESCE(afternoon_yield, 0.0)
                        + COALESCE(evening_yield, 0.0)
                    )
                ) <= 0.000001
            )
        )
    )
)
"""


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
        # Repository/API code recalculates the total, but the authoritative
        # ledger must also reject malformed direct SQL/ORM writes. Governed
        # rows require component/total integrity. Legacy non-governed rows
        # may retain a historical total without session components, but still
        # cannot contain non-finite or negative values.
        CheckConstraint(
            _MILK_GOVERNED_INTEGRITY,
            name="ck_milk_production_yield_integrity",
        ),
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
        numeric_values = []
        for value in entered:
            numeric_value = float(value)
            if not isfinite(numeric_value) or numeric_value < 0:
                raise ValueError(
                    "Milk yields must be finite, non-negative numbers."
                )
            numeric_values.append(numeric_value)
        self.total_yield = sum(numeric_values) if numeric_values else None
        return self.total_yield
