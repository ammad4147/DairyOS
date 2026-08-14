from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from ..database.base import Base
from dairyos.core.time_utils import utcnow


class HealthCase(Base):
    """A real animal health case, wrapping observations and treatments (G5.1).

    Before this model existed, `GET /health` was a 4-line system heartbeat
    (not animal data at all), and the real health surface --
    `HealthObservation` -- had no status-transition endpoint: an
    observation could be recorded, but nothing modeled "this animal is
    currently being treated for X, watch it until Y, here's how it was
    resolved." Two independent read paths existed over the raw
    observation data (`GET /health-observations`, event-journal-backed; vs
    `factory.health().get_all()`, used directly by farm_intelligence.py and
    dairy_kpi.py) but neither had any concept of a case.

    Decision (build-spec Session 5, DairyOS_Build_Specification.md Ch.5):
    build a real `HealthCase` entity, its own `HL-YYMMDD-NNN` ID, wrapping
    observations[] + diagnosis + treatments[] + withdrawal_until +
    follow_up_due_at + resolution. Resolution is an explicit operator
    action, not inferred.

    `HealthObservation` and `TreatmentRecord` each gained a nullable
    `health_case_id` column (see their own migrations/models) so existing
    write paths keep working unlinked, while `POST /farm/health-observations`
    and `POST /farm/treatments` can optionally attach a record to an open
    case. When a linked treatment's `milk_withdrawal_until` is later than
    the case's own, the case's `withdrawal_until` is raised to match --
    the case always reflects the latest known withdrawal date across
    everything wrapped into it, never a stale independent value.

    `severity` is governed (`GOVERNED["health_severities"]`); `status` is
    governed too (`GOVERNED["health_case_statuses"]`: OPEN/RESOLVED).
    """

    __tablename__ = "health_cases"

    id = Column(Integer, primary_key=True, autoincrement=True)

    case_id = Column(String, nullable=False, unique=True)

    animal_id = Column(String, nullable=False, index=True)

    severity = Column(String, nullable=False)

    diagnosis = Column(String, nullable=True)

    notes = Column(String, nullable=True)

    status = Column(String, nullable=False, default="OPEN")

    opened_at = Column(DateTime, nullable=False, default=utcnow)

    opened_by = Column(String, nullable=True)

    follow_up_due_at = Column(DateTime, nullable=True)

    withdrawal_until = Column(DateTime, nullable=True)

    resolution = Column(String, nullable=True)

    resolved_at = Column(DateTime, nullable=True)

    resolved_by = Column(String, nullable=True)
