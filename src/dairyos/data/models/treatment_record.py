"""Persisted veterinary treatment record.

Sprint / Gap-analysis Tier 1a
=============================

Fixes the core Tier 1a safety defect: there was no API endpoint that
recorded a treatment, so `WithdrawalService.add_period()` was never
called and the milk-withdrawal safety check in
`api/farm_data_entry.py::record_milk_entry` could never trigger.

Every row here is also replayed into the in-memory `WithdrawalService`
at application startup (see `ApplicationRuntime._hydrate_withdrawal_periods`)
so active withdrawal periods survive an application restart.
"""

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
)

from datetime import datetime

from ..database.base import Base


class TreatmentRecord(Base):

    __tablename__ = "treatment_record"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    animal_id = Column(
        String,
        nullable=False,
        index=True,
    )

    diagnosis = Column(
        String,
        nullable=True,
    )

    medicine = Column(
        String,
        nullable=False,
    )

    dose = Column(
        String,
        nullable=True,
    )

    treated_by = Column(
        String,
        nullable=True,
    )

    treated_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    milk_withdrawal_days = Column(
        Float,
        nullable=False,
    )

    milk_withdrawal_until = Column(
        DateTime,
        nullable=False,
    )

    #
    # True when the withdrawal period used was not found in the
    # maintained drug reference table and had to be supplied directly
    # on the treatment request. Surfaced in the UI/API so the farm
    # knows to add the drug to the reference table.
    #
    withdrawal_source = Column(
        String,
        default="reference_table",
        nullable=False,
    )

    notes = Column(
        String,
        nullable=True,
    )
