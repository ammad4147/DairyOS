"""Date-based individual-animal milk decline detection.

The alert denominator is deliberately the animal's COMPLETE daily yield on
one production date versus that same animal's complete daily yield on the
immediately preceding production date. It is not a session comparison, a
command-view snapshot, or a farm-total comparison.

The function remains pure over record-shaped dictionaries. Callers supply the
animal's governed milking frequency so completeness is evaluated against the
animal's actual two- or three-session cycle.
"""

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


def detect_drop(
    records: list[dict],
    *,
    animal_id: str,
    session: str | None = None,
    as_of_date: date,
    milking_frequency: str | None = None,
    expected_sessions: tuple[str, ...] | None = None,
) -> dict | None:
    """Compare one animal's complete daily yield with the prior date.

    ``session`` is retained as a compatibility argument for existing callers,
    but it is deliberately ignored for the comparison denominator.

    Returns ``None`` when the current date is incomplete, the immediately
    preceding date is absent/incomplete, or the prior total is not positive.
    Otherwise returns the two date totals, percentage movement, and any
    missing-session information for the current date.

    Severity:
        decline < 10%       -> None
        10% <= decline <= 20% -> HIGH (amber)
        decline > 20%       -> CRITICAL (red)
    """

    frequency = milking_frequency
    if expected_sessions is not None:
        expected = tuple(expected_sessions)
        frequency = "THRICE_DAILY" if len(expected) == 3 else "TWICE_DAILY" if len(expected) == 2 else None

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

    current_missing = missing_sessions(current_row, frequency)
    if not is_complete(current_row, frequency):
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

    previous_date = date.fromordinal(as_of_date.toordinal() - 1)
    previous_row = next(
        (record for record in eligible if record_date(record) == previous_date),
        None,
    )

    if previous_row is None or not is_complete(previous_row, frequency):
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
