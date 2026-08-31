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
        for field in (
            "morning_yield",
            "afternoon_yield",
            "evening_yield",
        )
    ) or record.get("total_yield") is not None


def _previous_production_row(
    eligible: list[dict],
    as_of_date: date,
):
    """Return the immediately preceding recorded production date."""
    prior = [
        record
        for record in eligible
        if (
            production_date := record_date(record)
        ) is not None
        and production_date < as_of_date
    ]

    if not prior:
        return None

    return max(
        prior,
        key=lambda record: record_date(record),
    )


def _merge_daily_rows(
    records: list[dict],
    *,
    animal_id: str,
    production_date: date,
) -> dict | None:
    """Reconstruct one animal/day from session-level production rows."""
    matching = [
        record
        for record in records
        if str(record.get("animal_id")) == str(animal_id)
        and record.get("session_ledger") is True
        and str(record.get("status", "")).upper() != "NOT_MILKED"
        and record_date(record) == production_date
        and _has_entered_yield(record)
    ]

    if not matching:
        return None

    if len(matching) == 1:
        return dict(matching[0])

    merged = {
        "animal_id": str(animal_id),
        "production_date": production_date.isoformat(),
        "session_ledger": True,
        "status": "MILKED",
        "morning_yield": None,
        "afternoon_yield": None,
        "evening_yield": None,
        "total_yield": None,
    }

    for record in matching:
        for field in (
            "morning_yield",
            "afternoon_yield",
            "evening_yield",
        ):
            value = record.get(field)

            if value is None:
                continue

            if merged[field] is None:
                merged[field] = float(value)

    entered = [
        merged[field]
        for field in (
            "morning_yield",
            "afternoon_yield",
            "evening_yield",
        )
        if merged[field] is not None
    ]

    merged["total_yield"] = (
        float(sum(entered))
        if entered
        else None
    )

    return merged


def _daily_rows(
    eligible: list[dict],
    *,
    animal_id: str,
) -> list[dict]:
    """Collapse session-level rows into one row per production date."""
    dates = sorted(
        {
            production_date
            for record in eligible
            if (
                production_date := record_date(record)
            ) is not None
        }
    )

    rows = []

    for production_date in dates:
        row = _merge_daily_rows(
            eligible,
            animal_id=animal_id,
            production_date=production_date,
        )

        if row is not None:
            rows.append(row)

    return rows


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
    """Compare complete daily yield with the preceding comparable day.

    Approved DairyOS milk-decline thresholds:

        decline < 10%   -> no finding
        10% through 20% -> HIGH
        decline > 20%   -> CRITICAL

    These thresholds are percentage thresholds only. No alternate
    AMBER/RED severity vocabulary is used.
    """
    current_frequency = milking_frequency
    previous_frequency = milking_frequency

    if schedule_service is not None:
        if animal is None:
            raise ValueError(
                "animal is required when schedule_service is supplied"
            )

        current_frequency = (
            schedule_service.get_frequency_for_date(
                animal,
                as_of_date,
            )
        )

    elif expected_sessions is not None:
        expected = tuple(expected_sessions)

        current_frequency = (
            "THRICE_DAILY"
            if len(expected) == 3
            else "TWICE_DAILY"
            if len(expected) == 2
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

    daily_rows = _daily_rows(
        eligible,
        animal_id=animal_id,
    )

    current_row = next(
        (
            record
            for record in daily_rows
            if record_date(record) == as_of_date
        ),
        None,
    )

    if current_row is None:
        return None

    current_missing = missing_sessions(
        current_row,
        current_frequency,
    )

    if not is_complete(
        current_row,
        current_frequency,
    ):
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

    previous_row = _previous_production_row(
        daily_rows,
        as_of_date,
    )

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
        previous_frequency = (
            schedule_service.get_frequency_for_date(
                animal,
                previous_date,
            )
        )

    if not is_complete(
        previous_row,
        previous_frequency,
    ):
        return {
            "severity": None,
            "status": "NO_COMPARABLE_PRIOR_DATE",
            "current": daily_total(current_row),
            "previous": None,
            "percent": None,
            "current_date": as_of_date.isoformat(),
            "previous_date": (
                previous_date.isoformat()
                if previous_date is not None
                else None
            ),
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

    percent = round(
        ((current - previous) / previous) * 100,
        1,
    )

    # APPROVED THRESHOLDS - DO NOT CHANGE.
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
