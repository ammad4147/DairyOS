"""Persisted per-animal milk production record.

G1.6 data-integrity boundary
============================

The three yield columns are **nullable with no default**. This is deliberate
and load-bearing:

* ``NULL``  = nobody entered a figure for this session.
* ``0.0``   = an operator looked at the animal and recorded that it gave zero.

Defaulting the columns to ``0.0`` made those two states indistinguishable, so
every herd average silently absorbed sessions that were never entered and any
drop-detection built on top would fire on missing data. Nothing downstream may
re-introduce a default here.
"""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    func,
)
from datetime import datetime

from ..database.base import Base


class MilkProduction(Base):


    __tablename__ = "milk_production"


    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )


    animal_id = Column(
        String,
        nullable=False
    )


    # When the milk was produced.
    production_date = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )


    # When the operator entered it. Distinct from production_date so that a
    # backfilled record is visibly a backfill.
    recorded_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )


    # The selected milking session is now persisted with the production
    # record.  It is nullable only for legacy rows created before G3.1;
    # all new API writes require a governed session value.
    milking_session = Column(
        String,
        nullable=True
    )


    # True when this row was written through the governed session ledger.
    # Pre-ledger history stays False and is excluded from sequencing, from
    # the one-record-per-animal-per-day constraint, and from drop detection.
    session_ledger = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false"
    )


    morning_yield = Column(
        Float,
        nullable=True
    )


    afternoon_yield = Column(
        Float,
        nullable=True
    )


    evening_yield = Column(
        Float,
        nullable=True
    )


    total_yield = Column(
        Float,
        nullable=True
    )


    status = Column(
        String,
        default="RECORDED"
    )


    # PARTIAL unique index, not a total one: real history contains genuine
    # duplicate animal-days, so a total index could not be created without
    # deleting operator records. Only governed ledger rows are constrained.
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
        """Only the session yields an operator actually supplied."""

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
        """True when at least one session yield was entered."""

        return bool(self.entered_yields)


    def calculate_total(self):
        """Sum the entered yields, preserving NULL when none were entered."""

        entered = self.entered_yields

        self.total_yield = (
            sum(entered)
            if entered
            else None
        )

        return self.total_yield
