from sqlalchemy import Column, Integer, String, DateTime

from ..database.base import Base
from dairyos.core.time_utils import utcnow


class OperationalFinding(Base):
    """The single cross-cutting entity behind the dashboard action queue,
    every section's alert list, and navigation count badges (AA-013 §4).

    Before this model existed, DairyOS had two independent, disagreeing
    notions of "something needs attention": `OperationalCommandCenterService`'s
    ad-hoc `OperationalDecision` (in-memory, regenerated from recommendations
    on every `/command-center` read, ids like `DEC-<hash>`) and each
    section's own ungoverned checks. AA-013 D-UI-5 requires one entity with
    one ID allocator. This is that entity -- the command-center decision
    lifecycle is left running as-is (it already has real acknowledge/resolve
    endpoints wired into the dashboard's Action Queue) rather than torn out
    in the same pass that introduces its replacement; detection engines
    write findings here going forward, and folding the two lifecycles
    together is tracked separately rather than risked as a single change
    that touches both at once.

    `finding_id` format: `<PREFIX>-YYMMDD-NNN`, one shared per-module
    per-day sequence -- the same scheme as HealthCase's `HL-YYMMDD-NNN`
    (G5.1) and the milking session ledger's `MS-YYMMDD-NNN` (G3.1).

    Re-detection of an already-open finding for the same underlying
    condition updates it (bumps `observation_count`, refreshes
    `detail`/`last_observed_at`) rather than raising a duplicate -- "one cow
    dropping for four consecutive days is one finding with four
    observations, not four alerts" (§4.4). Matched via `dedupe_key`, which a
    detection engine controls (e.g. `f"MILK_DROP:{animal_id}:{session}"`).

    Resolution requiring a note when severity is CRITICAL (§4.4) is enforced
    at the API layer (`api/operational_findings.py`), not here -- this model
    has no opinion on request validation.
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
