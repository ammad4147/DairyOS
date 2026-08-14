"""Maintained drug withdrawal reference table.

Sprint / Gap-analysis Tier 1a
=============================

This is the farm's maintained lookup of medicines and their milk
withdrawal periods, used by the treatment-recording endpoint to
compute a safe withdrawal end time automatically.

Seed values shipped with DairyOS are conservative, widely-published
general veterinary reference points for common dairy treatments.
THEY ARE A STARTING POINT, NOT A SUBSTITUTE FOR THE ACTUAL PRODUCT
LABEL OR A VETERINARIAN'S DIRECTIVE. Farm staff must verify and, if
necessary, correct each entry (via GET/POST /farm/drug-reference)
against the label of the exact product in use before relying on it
for a real withholding decision. Withdrawal periods vary by country,
manufacturer, dose route and dose rate even for the "same" drug.
"""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
)

from datetime import datetime

from ..database.base import Base
from dairyos.core.time_utils import utcnow


class DrugWithdrawalReference(Base):

    __tablename__ = "drug_withdrawal_reference"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    #
    # Matched case-insensitively against the treatment's
    # `medicine` field.
    #
    medicine = Column(
        String,
        nullable=False,
        unique=True,
        index=True,
    )

    milk_withdrawal_days = Column(
        Float,
        nullable=False,
    )

    meat_withdrawal_days = Column(
        Float,
        nullable=True,
    )

    notes = Column(
        String,
        nullable=True,
    )

    #
    # False for entries auto-loaded from the shipped seed set, so the
    # UI/API can flag them as "verify before relying on this" until a
    # human confirms them against the actual product label.
    #
    verified = Column(
        Boolean,
        default=False,
        nullable=False,
    )

    updated_by = Column(
        String,
        nullable=True,
    )

    updated_at = Column(
        DateTime,
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )
