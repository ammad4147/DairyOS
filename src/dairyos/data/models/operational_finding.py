from sqlalchemy import Column, Integer, String, DateTime

from ..database.base import Base
from dairyos.core.time_utils import utcnow


class OperationalFinding(Base):
    """The single cross-cutting entity behind the dashboard action queue,
    every section's alert list, and navigation count badges (AA-013 §4).

    Findings are raised by detection engines and persist their complete
    lifecycle, including operator resolution and administrator reinstatement.
    """

    __tablename__ = "operational_findings"

    id = Column(Integer, primary_key=True, autoincrement=True)

    finding_id = Column(String, nullable=False, unique=True, index=True)
    source_module = Column(String, nullable=False, index=True)

    subject_type = Column(String, nullable=True)
    subject_id = Column(String, nullable=True, index=True)

    severity = Column(String, nullable=False)
    title = Column(String, nullable=False)
    detail = Column(String, nullable=True)
    status = Column(String, nullable=False, default="RAISED", index=True)
    route = Column(String, nullable=True)

    dedupe_key = Column(String, nullable=True, index=True)
    observation_count = Column(Integer, nullable=False, default=1)

    raised_at = Column(DateTime, nullable=False, default=utcnow)
    last_observed_at = Column(DateTime, nullable=False, default=utcnow)

    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String, nullable=True)

    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String, nullable=True)
    resolution_note = Column(String, nullable=True)

    reinstated_at = Column(DateTime, nullable=True)
    reinstated_by = Column(String, nullable=True)
    reinstate_reason = Column(String, nullable=True)
