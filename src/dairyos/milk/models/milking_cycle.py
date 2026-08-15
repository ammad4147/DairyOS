"""Explicit, date-based milking-cycle rules."""

from dataclasses import dataclass, field
from datetime import date, datetime, time, timezone
from enum import Enum
from typing import Dict, List, Optional


class MilkingFrequency(int, Enum):
    TWICE_DAILY = 2
    THRICE_DAILY = 3
    THREE_TIMES_DAILY = 3


DEFAULT_SESSION_TIMES = {
    "MORNING": time(6, 0),
    "AFTERNOON": time(14, 0),
    "EVENING": time(21, 0),
}


def normalize_frequency(value) -> MilkingFrequency:
    if isinstance(value, MilkingFrequency):
        return value
    if isinstance(value, int):
        return MilkingFrequency(value)
    normalized = str(value).strip().upper().replace("-", "_").replace(" ", "_")
    aliases = {
        "2": MilkingFrequency.TWICE_DAILY,
        "TWICE": MilkingFrequency.TWICE_DAILY,
        "TWICE_DAILY": MilkingFrequency.TWICE_DAILY,
        "2X": MilkingFrequency.TWICE_DAILY,
        "3": MilkingFrequency.THRICE_DAILY,
        "THRICE": MilkingFrequency.THRICE_DAILY,
        "THRICE_DAILY": MilkingFrequency.THRICE_DAILY,
        "THREE_TIMES": MilkingFrequency.THRICE_DAILY,
        "THREE_TIMES_DAILY": MilkingFrequency.THRICE_DAILY,
        "3X": MilkingFrequency.THRICE_DAILY,
    }
    try:
        return aliases[normalized]
    except KeyError as exc:
        raise ValueError("milking frequency must be 2 or 3 sessions per day") from exc


@dataclass(frozen=True)
class MilkingCycle:
    animal_id: str
    frequency: MilkingFrequency | str | int
    effective_from: date
    session_times: Dict[str, time] = field(default_factory=lambda: dict(DEFAULT_SESSION_TIMES))
    active: bool = True

    def __post_init__(self):
        if not str(self.animal_id).strip():
            raise ValueError("animal_id is required")
        normalized = normalize_frequency(self.frequency)
        object.__setattr__(self, "frequency", normalized)
        if self.session_times == DEFAULT_SESSION_TIMES and normalized == MilkingFrequency.TWICE_DAILY:
            object.__setattr__(self, "session_times", {"MORNING": DEFAULT_SESSION_TIMES["MORNING"], "EVENING": DEFAULT_SESSION_TIMES["EVENING"]})
        required = ["MORNING", "EVENING"]
        if normalized == MilkingFrequency.THRICE_DAILY:
            required.insert(1, "AFTERNOON")
        missing = [session for session in required if session not in self.session_times]
        if missing:
            raise ValueError(f"missing scheduled milking session times: {', '.join(missing)}")
        if len(self.session_times) != int(normalized):
            raise ValueError("session_times must contain exactly the configured 2 or 3 sessions")

    @property
    def sessions(self) -> List[str]:
        return sorted(self.session_times, key=lambda name: self.session_times[name])

    @property
    def animal_status(self) -> str:
        return "MILKING" if self.active else "NOT_MILKING"

    def applies_to(self, operational_date: date) -> bool:
        return self.active and operational_date >= self.effective_from

    def expected_sessions(self, operational_date: date) -> List[dict]:
        if not self.applies_to(operational_date):
            return []
        return [
            {
                "animal_id": self.animal_id,
                "animal_status": self.animal_status,
                "milking_frequency": self.frequency.name,
                "operational_date": operational_date.isoformat(),
                "shift": session,
                "scheduled_at": datetime.combine(operational_date, self.session_times[session], tzinfo=timezone.utc).isoformat(),
                "status": "EXPECTED",
            }
            for session in self.sessions
        ]

    def expected_session(self, operational_date: date, session: str) -> Optional[dict]:
        return next((item for item in self.expected_sessions(operational_date) if item["shift"] == session.upper()), None)


def classify_session_entry(expected_session: dict, recorded_at: datetime) -> dict:
    """Return session outcome metadata without creating a milk production record."""
    scheduled_at = datetime.fromisoformat(expected_session["scheduled_at"])
    if recorded_at.tzinfo is None:
        recorded_at = recorded_at.replace(tzinfo=timezone.utc)
    return {**expected_session, "recorded_at": recorded_at.isoformat(), "late": recorded_at > scheduled_at, "status": "RECORDED"}
