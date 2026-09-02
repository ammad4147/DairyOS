from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from ..database.base import Base
from dairyos.core.time_utils import utcnow


class OperationalFindingLifecycleEvent(Base):
    # Immutable audit event for an OperationalFinding lifecycle transition.

    __tablename__ = "operational_finding_lifecycle_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    finding_id = Column(
        String,
        ForeignKey("operational_findings.finding_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    event_type = Column(String, nullable=False, index=True)
    occurred_at = Column(DateTime, nullable=False, default=utcnow, index=True)
    operator = Column(String, nullable=True)
    note = Column(String, nullable=True)
    linked_event_id = Column(
        Integer,
        ForeignKey(
            "operational_finding_lifecycle_events.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
        index=True,
    )
