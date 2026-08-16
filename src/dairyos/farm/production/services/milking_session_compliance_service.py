"""Authoritative session-compliance read model for one animal/date."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable, Mapping

from dairyos.farm.herd.services.animal_milking_schedule_service import (
    AnimalMilkingScheduleService,
)
from dairyos.farm.production.services.milk_daily_semantics import (
    evaluate_sessions,
)

RECORDED = "RECORDED"
SKIPPED = "SKIPPED"
MISSING = "MISSING"


@dataclass(frozen=True)
class SessionCompliance:
    animal_id: str
    operational_date: date
    effective_frequency: str | None
    expected_sessions: tuple[str, ...]
    session_states: Mapping[str, str]
    completed_sessions: tuple[str, ...]
    skipped_sessions: tuple[str, ...]
    missing_sessions: tuple[str, ...]
    compliance_percentage: float | None
    status: str

    def as_dict(self) -> dict:
        return {
            "animal_id": self.animal_id,
            "operational_date": self.operational_date.isoformat(),
            "effective_frequency": self.effective_frequency,
            "expected_sessions": list(self.expected_sessions),
            "session_states": dict(self.session_states),
            "completed_sessions": list(self.completed_sessions),
            "skipped_sessions": list(self.skipped_sessions),
            "missing_sessions": list(self.missing_sessions),
            "compliance_percentage": self.compliance_percentage,
            "status": self.status,
        }


class MilkingSessionComplianceService:
    """Resolve expected sessions and admissible outcomes for an animal/date."""

    def __init__(self, animal_repository):
        self.schedule_service = AnimalMilkingScheduleService(
            animal_repository
        )

    @staticmethod
    def _as_date(value: date | datetime | str) -> date:
        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        return date.fromisoformat(str(value))

    @staticmethod
    def _record_to_dict(record):
        if record is None:
            return None

        return {
            "animal_id": getattr(record, "animal_id", None),
            "production_date": getattr(record, "production_date", None),
            "session_ledger": getattr(record, "session_ledger", False),
            "status": getattr(record, "status", None),
            "morning_yield": getattr(record, "morning_yield", None),
            "afternoon_yield": getattr(record, "afternoon_yield", None),
            "evening_yield": getattr(record, "evening_yield", None),
            "total_yield": getattr(record, "total_yield", None),
        }

    def evaluate(
        self,
        *,
        animal,
        operational_date: date | datetime | str,
        record=None,
        skipped_sessions: Iterable[str] | None = None,
    ) -> SessionCompliance:
        op_date = self._as_date(operational_date)

        snapshot = self.schedule_service.get_schedule_snapshot(
            animal,
            operational_date=op_date,
        )

        semantics = evaluate_sessions(
            self._record_to_dict(record),
            snapshot.milking_frequency,
            skipped_sessions=skipped_sessions,
        )

        return SessionCompliance(
            animal_id=str(animal.animal_id),
            operational_date=op_date,
            effective_frequency=snapshot.milking_frequency,
            expected_sessions=tuple(
                semantics["expected_sessions"]
            ),
            session_states=dict(
                semantics["session_states"]
            ),
            completed_sessions=tuple(
                semantics["completed_sessions"]
            ),
            skipped_sessions=tuple(
                semantics["skipped_sessions"]
            ),
            missing_sessions=tuple(
                semantics["missing_sessions"]
            ),
            compliance_percentage=semantics[
                "compliance_percentage"
            ],
            status=semantics["status"],
        )
