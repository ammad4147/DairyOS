"""Shared date-based semantics for governed milk production."""

from __future__ import annotations

from datetime import date, datetime

from .animal_milking_schedule_service import FREQUENCY_SESSIONS


SESSION_FIELDS = {
    "MORNING": "morning_yield",
    "AFTERNOON": "afternoon_yield",
    "EVENING": "evening_yield",
}


def expected_sessions(frequency: str | None) -> tuple[str, ...]:
    """Return governed sessions from the central schedule vocabulary.

    This helper remains for compatibility with existing callers. Historical
    date interpretation belongs to AnimalMilkingScheduleService; callers
    answering an animal/date question must resolve the frequency there first.
    """
    if frequency is None:
        return ()
    return FREQUENCY_SESSIONS.get(str(frequency).strip().upper(), ())


def record_date(record: dict) -> date | None:
    raw = record.get("production_date")
    if not raw:
        return None
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, date):
        return raw
    try:
        return datetime.fromisoformat(str(raw)[:10]).date()
    except ValueError:
        return None


def entered_sessions(record: dict) -> tuple[str, ...]:
    return tuple(
        session
        for session, field in SESSION_FIELDS.items()
        if record.get(field) is not None
    )


def missing_sessions(record: dict, frequency: str | None) -> tuple[str, ...]:
    expected = expected_sessions(frequency)
    entered = set(entered_sessions(record))
    return tuple(session for session in expected if session not in entered)


def is_complete(record: dict, frequency: str | None) -> bool:
    """True only when every expected session has an entered yield.

    A NULL yield is never treated as zero. A declared NOT_MILKED record is
    not a production row and therefore cannot make an animal's milk day
    complete; that fact is handled by the session ledger separately.
    """
    if record.get("session_ledger") is not True:
        return False
    if str(record.get("status", "")).upper() == "NOT_MILKED":
        return False
    expected = expected_sessions(frequency)
    return bool(expected) and not missing_sessions(record, frequency)


def daily_total(record: dict) -> float:
    total = record.get("total_yield")
    if total is not None:
        return float(total)
    return sum(
        float(record[field])
        for field in SESSION_FIELDS.values()
        if record.get(field) is not None
    )
