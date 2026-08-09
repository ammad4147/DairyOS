"""
Persistent operational event journal model.

Sprint-038
==========

The event journal is the durable append-only record of operational
events.

It is intentionally separate from OperationalEventModel:

EventJournalModel
    = original persisted event + payload for replay/audit

OperationalEventModel
    = operational database projection used by application queries
"""

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    JSON,
    String,
)

from dairyos.data.database.base import Base


class EventJournalModel(Base):
    """
    PostgreSQL persistence model for the operational event journal.
    """

    __tablename__ = "event_journal"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    event_id = Column(
        String,
        nullable=False,
        index=True,
    )

    event_type = Column(
        String,
        nullable=False,
        index=True,
    )

    timestamp = Column(
        DateTime,
        nullable=False,
        index=True,
    )

    payload = Column(
        JSON,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
