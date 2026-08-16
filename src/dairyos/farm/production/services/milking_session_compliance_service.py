"""Authoritative session-compliance read model for one animal/date."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable, Mapping

from dairyos.farm.herd.services.animal_milking_schedule_service import AnimalMilkingScheduleService

RECORDED = "RECORDED"
SKIPPED = "SKIPPED"
MISSING = "MISSING"
WITHHELD = "WITHHELD"

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
    withheld_sessions: tuple[str, ...]
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
            "withheld_sessions": list(self.withheld_sessions),
            "compliance_percentage": self.compliance_percentage,
            "status": self.status,
        }

class MilkingSessionComplianceService:
    """Resolve expected sessions and admissible outcomes for an animal/date."""
    def __init__(self, animal_repository):
        self.schedule_service = AnimalMilkingScheduleService(animal_repository)

    @staticmethod
    def _as_date(value: date | datetime | str) -> date:
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        return date.fromisoformat(str(value))

    @staticmethod
    def _recorded_sessions(record) -> set[str]:
        fields = {"MORNING": "morning_yield", "AFTERNOON": "afternoon_yield", "EVENING": "evening_yield"}
        return {session for session, field in fields.items() if getattr(record, field, None) is not None}

    def evaluate(self, *, animal, operational_date: date | datetime | str, record=None, skipped_sessions: Iterable[str] | None = None) -> SessionCompliance:
        op_date = self._as_date(operational_date)
        snapshot = self.schedule_service.get_schedule_snapshot(animal, operational_date=op_date)
        expected = snapshot.expected_sessions
        skipped = {str(value).strip().upper() for value in (skipped_sessions or ())}
        recorded = self._recorded_sessions(record) if record is not None else set()
        withheld = set()
        if record is not None and str(getattr(record, "status", "")).upper() == WITHHELD:
            withheld = recorded & set(expected)

        states = {}
        for session in expected:
            if session in withheld:
                states[session] = WITHHELD
            elif session in recorded:
                states[session] = RECORDED
            elif session in skipped:
                states[session] = SKIPPED
            else:
                states[session] = MISSING

        completed = tuple(session for session in expected if states[session] in {RECORDED, SKIPPED, WITHHELD})
        skipped_expected = tuple(session for session in expected if states[session] == SKIPPED)
        missing = tuple(session for session in expected if states[session] == MISSING)
        withheld_expected = tuple(session for session in expected if states[session] == WITHHELD)
        percentage = None if not expected else round((len(completed) / len(expected)) * 100, 1)

        if not expected:
            status = "NO_GOVERNED_FREQUENCY"
        elif missing:
            status = "INCOMPLETE"
        elif withheld_expected:
            status = "COMPLETE_WITH_WITHHELD"
        else:
            status = "COMPLETE"

        return SessionCompliance(
            animal_id=str(animal.animal_id), operational_date=op_date,
            effective_frequency=snapshot.milking_frequency,
            expected_sessions=expected, session_states=states,
            completed_sessions=completed, skipped_sessions=skipped_expected,
            missing_sessions=missing, withheld_sessions=withheld_expected,
            compliance_percentage=percentage, status=status,
        )
