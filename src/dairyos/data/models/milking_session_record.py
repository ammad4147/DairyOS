"""Herd-level record of what happened to one milking session.

Why this is a separate table
============================

``Not milked`` is a statement about the *session*, not about each animal. On a
286-animal farm, expressing it on ``milk_production`` would mean writing 286
rows to say that nothing happened -- and those rows would then have to be
excluded from every average, every count and every drop calculation. One row
per (date, session) states the same fact once and keeps the per-animal table
meaning only "milk was measured".
"""

from datetime import datetime

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Integer,
    String,
    UniqueConstraint,
)

from ..database.base import Base


class MilkingSessionRecord(Base):


    __tablename__ = "milking_session_records"


    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )


    # Operator-facing identity: MS-YYMMDD-NNN
    session_record_id = Column(
        String,
        nullable=False,
        unique=True
    )


    operational_date = Column(
        Date,
        nullable=False
    )


    milking_session = Column(
        String,
        nullable=False
    )


    # RECORDED | NOT_MILKED
    status = Column(
        String,
        nullable=False
    )


    # Governed MilkingSessionSkipReason, required for NOT_MILKED only.
    reason = Column(
        String,
        nullable=True
    )


    notes = Column(
        String,
        nullable=True
    )


    recorded_by = Column(
        String,
        nullable=True
    )


    recorded_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )


    # One statement per session per day. A farm cannot simultaneously report
    # that a session was milked and not milked.
    __table_args__ = (
        UniqueConstraint(
            "operational_date",
            "milking_session",
            name="uq_milking_session_records_date_session",
        ),
    )


    def __repr__(self) -> str:
        return (
            f"<MilkingSessionRecord {self.session_record_id} "
            f"{self.operational_date} {self.milking_session} "
            f"{self.status}>"
        )
