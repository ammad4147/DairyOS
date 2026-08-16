"""Shared date-based semantics for governed milk production."""

from __future__ import annotations

from datetime import date, datetime

from dairyos.farm.herd.services.animal_milking_schedule_service import (
    FREQUENCY_MAP,
)

SESSION_FIELDS = {
    "MORNING": "morning_yield",
    "AFTERNOON": "afternoon_yield",
    "EVENING": "evening_yield",
}

RECORDED = "RECORDED"
SKIPPED = "SKIPPED"
MISSING = "MISSING"
WITHHELD = "WITHHELD"


def expected_sessions(frequency: str | None) -> tuple[str, ...]:
    """Return governed sessions for an already-resolved frequency."""
    if frequency is None:
        return ()
    return FREQUENCY_MAP.get(
        str(frequency).strip().upper(),
        (),
    )


def record_date(record: dict) -> date | None:
    raw = record.get("production_date")
    if not raw:
        return None

    if isinstance(raw, datetime):
        return raw.date()

    if isinstance(raw, date):
        return raw

    try:
        return datetime.fromisoformat(
            str(raw)[:10]
        ).date()
    except ValueError:
        return None


def entered_sessions(record: dict) -> tuple[str, ...]:
    return tuple(
        session
        for session, field in SESSION_FIELDS.items()
        if record.get(field) is not None
    )


def evaluate_sessions(
    record: dict | None,
    frequency: str | None,
    skipped_sessions=(),
) -> dict:
    """Resolve one animal/date session state without turning NULL into zero."""
    expected = expected_sessions(frequency)

    skipped = {
        str(value).strip().upper()
        for value in (skipped_sessions or ())
    }

    entered = set(
        entered_sessions(record or {})
    )

    status = str(
        (record or {}).get("status", "")
        or ""
    ).upper()

    states = {}

    for session in expected:
        if session in entered and status == WITHHELD:
            states[session] = WITHHELD
        elif session in entered:
            states[session] = RECORDED
        elif session in skipped:
            states[session] = SKIPPED
        else:
            states[session] = MISSING

    completed = tuple(
        session
        for session in expected
        if states[session] in {
            RECORDED,
            SKIPPED,
            WITHHELD,
        }
    )

    skipped_expected = tuple(
        session
        for session in expected
        if states[session] == SKIPPED
    )

    missing = tuple(
        session
        for session in expected
        if states[session] == MISSING
    )

    withheld_expected = tuple(
        session
        for session in expected
        if states[session] == WITHHELD
    )

    if not expected:
        status_name = "NO_GOVERNED_FREQUENCY"
    elif missing:
        status_name = "INCOMPLETE"
    elif withheld_expected:
        status_name = "COMPLETE_WITH_WITHHELD"
    else:
        status_name = "COMPLETE"

    compliance_percentage = (
        None
        if not expected
        else round(
            (len(completed) / len(expected)) * 100,
            1,
        )
    )

    return {
        "expected_sessions": expected,
        "session_states": states,
        "completed_sessions": completed,
        "skipped_sessions": skipped_expected,
        "missing_sessions": missing,
        "withheld_sessions": withheld_expected,
        "compliance_percentage": compliance_percentage,
        "status": status_name,
    }


def missing_sessions(
    record: dict,
    frequency: str | None,
) -> tuple[str, ...]:
    return tuple(
        evaluate_sessions(
            record,
            frequency,
        )["missing_sessions"]
    )


def is_complete(
    record: dict,
    frequency: str | None,
) -> bool:
    """A day is complete only when every expected session has an admissible outcome."""
    result = evaluate_sessions(
        record,
        frequency,
    )
    return (
        bool(result["expected_sessions"])
        and not result["missing_sessions"]
    )


def daily_total(record: dict) -> float:
    total = record.get("total_yield")

    if total is not None:
        return float(total)

    return sum(
        float(record[field])
        for field in SESSION_FIELDS.values()
        if record.get(field) is not None
    )

