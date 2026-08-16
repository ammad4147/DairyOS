"""Date-based individual-animal milk decline detection."""

from datetime import date

from dairyos.farm.production.services.milk_daily_semantics import (
    daily_total,
    is_complete,
    missing_sessions,
    record_date,
)


def _has_entered_yield(record: dict) -> bool:
    return any(
        record.get(field) is not None
        for field in ("morning_yield", "afternoon_yield", "evening_yield")
    ) or record.get("total_yield") is not None


def _previous_production_row(eligible: list[dict], as_of_date: date):
    """Return the immediately preceding recorded production date, not merely yesterday."""
    prior = [
        record for record in eligible
        if (production_date := record_date(record)) is not None
        and production_date < as_of_date
    ]
    if not prior:
        return None
    return max(prior, key=lambda record: record_date(record))


def detect_drop(
    records: list[dict],
    *,
    animal_id: str,
    session: str | None = None,
    as_of_date: date,
    milking_frequency: str | None = None,
    expected_sessions: tuple[str, ...] | None = None,
    schedule_service=None,
    animal=None,
) -> dict | None:
    """Compare an animal's complete daily yield with its immediately preceding production date.

    The authoritative path resolves the effective frequency independently for
    the current and immediately preceding production dates. Explicit frequency
    arguments remain compatibility inputs for legacy callers only.
    """
    current_frequency = milking_frequency
    previous_frequency = milking_frequency

    if schedule_service is not None:
        if animal is None:
            raise ValueError("animal is required when schedule_service is supplied")
        current_frequency = schedule_service.get_frequency_for_date(animal, as_of_date)
    elif expected_sessions is not None:
        expected = tuple(expected_sessions)
        current_frequency = (
            "THRICE_DAILY" if len(expected) == 3
            else "TWICE_DAILY" if len(expected) == 2
            else None
        )
        previous_frequency = current_frequency

    eligible = [
        record
        for record in records
        if str(record.get("animal_id")) == str(animal_id)
        and record.get("session_ledger") is True
        and str(record.get("status", "")).upper() != "NOT_MILKED"
        and _has_entered_yield(record)
    ]

    current_row = next(
        (record for record in eligible if record_date(record) == as_of_date),
        None,
    )
    if current_row is None:
        return None

    current_missing = missing_sessions(current_row, current_frequency)
    if not is_complete(current_row, current_frequency):
        return {
            "severity": None,
            "status": "INCOMPLETE",
            "current": daily_total(current_row),
            "previous": None,
            "percent": None,
            "current_date": as_of_date.isoformat(),
            "previous_date": None,
            "missing_sessions": list(current_missing),
        }

    previous_row = _previous_production_row(eligible, as_of_date)
    if previous_row is None:
        return {
            "severity": None,
            "status": "NO_COMPARABLE_PRIOR_DATE",
            "current": daily_total(current_row),
            "previous": None,
            "percent": None,
            "current_date": as_of_date.isoformat(),
            "previous_date": None,
            "missing_sessions": [],
        }

    previous_date = record_date(previous_row)
    if schedule_service is not None:
        previous_frequency = schedule_service.get_frequency_for_date(animal, previous_date)

    if not is_complete(previous_row, previous_frequency):
        return {
            "severity": None,
            "status": "NO_COMPARABLE_PRIOR_DATE",
            "current": daily_total(current_row),
            "previous": None,
            "percent": None,
            "current_date": as_of_date.isoformat(),
            "previous_date": previous_date.isoformat(),
            "missing_sessions": [],
        }

    current = daily_total(current_row)
    previous = daily_total(previous_row)

    if previous <= 0:
        return {
            "severity": None,
            "status": "NO_VALID_PRIOR_YIELD",
            "current": current,
            "previous": previous,
            "percent": None,
            "current_date": as_of_date.isoformat(),
            "previous_date": previous_date.isoformat(),
            "missing_sessions": [],
        }

    percent = round(((current - previous) / previous) * 100, 1)

    if percent > -10:
        severity = None
    elif percent >= -20:
        severity = "HIGH"
    else:
        severity = "CRITICAL"

    return {
        "severity": severity,
        "status": "COMPLETE",
        "current": current,
        "previous": previous,
        "percent": percent,
        "current_date": as_of_date.isoformat(),
        "previous_date": previous_date.isoformat(),
        "missing_sessions": [],
    }
