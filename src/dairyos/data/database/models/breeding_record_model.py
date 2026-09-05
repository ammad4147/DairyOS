"""
Sprint-039

SQLAlchemy persistence model for operational breeding records.

This model persists the farm.operations BreedingRecord contract.

It does NOT replace herd.reproduction BreedingRecord.
"""

from datetime import datetime, UTC

from sqlalchemy import (
    Column,
    DateTime,
    String,
)

from dairyos.data.database.base import Base


class BreedingRecordModel(Base):
    """
    PostgreSQL representation of operational breeding records.

    ``timestamp`` is nullable because legacy/imported operational records may
    legitimately lack an observed timestamp. Analytics and reproductive KPI
    projections must exclude such records from time-window calculations rather
    than inventing a date.
    """

    __tablename__ = "breeding_records"

    record_id = Column(
        String,
        primary_key=True,
        index=True,
    )

    animal_id = Column(
        String,
        nullable=False,
        index=True,
    )

    event_type = Column(
        String,
        nullable=False,
    )

    result = Column(
        String,
        nullable=False,
    )

    technician = Column(
        String,
        nullable=False,
    )

    semen_or_bull = Column(
        String,
        nullable=True,
    )

    notes = Column(
        String,
        nullable=True,
    )

    timestamp = Column(
        DateTime(timezone=True),
        nullable=True,
        default=lambda: datetime.now(UTC),
    )
