from __future__ import annotations

import calendar
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query

from dairyos.api.dairy_kpi import _has_entered_yield, _record_date
from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.farm.findings.services.operational_finding_service import (
    OperationalFindingService,
)

router = APIRouter(prefix="/farm/milk", tags=["Milk Production"])

_PERIOD_LABELS = {
    "7d": "7 Days",
    "30d": "30 Days",
    "3mo": "3 Months",
    "6mo": "6 Months",
    "year": "Year",
    "custom": "Custom",
}

_SESSION_ORDER = {
    "MORNING": 1,
    "AFTERNOON": 2,
    "EVENING": 3,
}

_SESSION_FIELDS = {
    "MORNING": "morning_yield",
    "AFTERNOON": "afternoon_yield",
    "EVENING": "evening_yield",
}


def _shift_months(day: date, months: int) -> date:
    absolute = day.year * 12 + (day.month - 1) + months
    year, month_index = divmod(absolute, 12)
    month = month_index + 1
    last_day = calendar.monthrange(year, month)[1]
    return day.replace(
        year=year,
        month=month,
        day=min(day.day, last_day),
    )


def _resolve_period(
    period: str,
    start_date: date | None,
    end_date: date | None,
):
    today = datetime.now(timezone.utc).date()

    if period not in _PERIOD_LABELS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unknown period '{period}'. Expected "
                "7d, 30d, 3mo, 6mo, year, or custom."
            ),
        )

    if period == "custom":
        if start_date is None or end_date is None:
            raise HTTPException(
                status_code=400,
                detail="custom period requires start_date and end_date",
            )
        if end_date < start_date:
            raise HTTPException(
                status_code=400,
                detail="end_date must be on or after start_date",
            )

        start = start_date
        end_inclusive = end_date

    elif period == "7d":
        start = today - timedelta(days=6)
        end_inclusive = today

    elif period == "30d":
        start = today - timedelta(days=29)
        end_inclusive = today

    elif period == "3mo":
        start = _shift_months(today, -3)
        end_inclusive = today

    elif period == "6mo":
        start = _shift_months(today, -6)
        end_inclusive = today

    else:
        start = _shift_months(today, -12)
        end_inclusive = today

    end_exclusive = end_inclusive + timedelta(days=1)
    days = (end_exclusive - start).days

    previous_start = start - timedelta(days=days)
    previous_end = start

    return (
        start,
        end_exclusive,
        previous_start,
        previous_end,
        days,
    )


def _qualifying_rows(
    records,
    start: datetime,
    end: datetime,
):
    """
    Only governed, observed milk contributes to section aggregates.

    G1.6 / AA-013 §2.3:
    - session_ledger=False is pre-ledger history and is excluded;
    - rows with no entered yield are excluded;
    - absence is never converted into zero.
    """
    rows = []

    for record in records:
        if not bool(getattr(record, "session_ledger", False)):
            continue

        if not _has_entered_yield(record):
            continue

        timestamp = _record_date(
            record,
            "production_date",
            "recorded_at",
        )

        if timestamp is None or not (start <= timestamp < end):
            continue

        rows.append(record)

    return rows


def _row_total(record) -> float:
    total = getattr(record, "total_yield", None)

    if total is not None:
        return float(total)

    return sum(
        float(value)
        for value in (
            getattr(record, "morning_yield", None),
            getattr(record, "afternoon_yield", None),
            getattr(record, "evening_yield", None),
        )
        if value is not None
    )


def _sum_entered(rows, field: str):
    values = [
        float(getattr(row, field))
        for row in rows
        if getattr(row, field, None) is not None
    ]

    return round(sum(values), 3) if values else None


def _trend(rows):
    daily = defaultdict(
        lambda: {
            "morning": 0.0,
            "afternoon": 0.0,
            "evening": 0.0,
            "total": 0.0,
            "animal_days": set(),
        }
    )

    for row in rows:
        timestamp = _record_date(
            row,
            "production_date",
            "recorded_at",
        )
        day = timestamp.date()

        item = daily[day]

        item["morning"] += float(
            getattr(row, "morning_yield", None) or 0.0
        )
        item["afternoon"] += float(
            getattr(row, "afternoon_yield", None) or 0.0
        )
        item["evening"] += float(
            getattr(row, "evening_yield", None) or 0.0
        )
        item["total"] += _row_total(row)
        item["animal_days"].add(str(row.animal_id))

    return [
        {
            "date": day.isoformat(),
            "morning": round(values["morning"], 3),
            "afternoon": round(values["afternoon"], 3),
            "evening": round(values["evening"], 3),
            "total": round(values["total"], 3),
            "observed_animals": len(values["animal_days"]),
        }
        for day, values in sorted(daily.items())
    ]


def _period_metrics(rows):
    total = (
        round(sum(_row_total(row) for row in rows), 3)
        if rows
        else None
    )

    trend = _trend(rows)
    observed_days = len(trend)

    animal_days = len(
        {
            (
                str(row.animal_id),
                _record_date(
                    row,
                    "production_date",
                    "recorded_at",
                ).date(),
            )
            for row in rows
        }
    )

    return {
        "total_liters": total,
        "average_liters_per_day": (
            round(total / observed_days, 3)
            if total is not None and observed_days
            else None
        ),
        "average_liters_per_cow": (
            round(total / animal_days, 3)
            if total is not None and animal_days
            else None
        ),
        "morning_liters": _sum_entered(
            rows,
            "morning_yield",
        ),
        "afternoon_liters": _sum_entered(
            rows,
            "afternoon_yield",
        ),
        "evening_liters": _sum_entered(
            rows,
            "evening_yield",
        ),
        "observed_days": observed_days,
        "animal_days_with_entered_yield": animal_days,
        "trend": trend,
    }


def _change_pct(current, previous):
    if (
        current is None
        or previous is None
        or previous <= 0
    ):
        return None

    return round(
        ((current - previous) / previous) * 100,
        2,
    )


def _drop_status(change_pct):
    if change_pct is None:
        return "UNKNOWN"

    if change_pct <= -20:
        return "RED"

    if change_pct <= -10:
        return "AMBER"

    return "GOOD"


def _same_session_table(
    today_rows,
    yesterday_rows,
):
    """
    D-UI-2: compare today's latest observed session with
    yesterday's same session, never a day-total proxy.
    """
    if not today_rows:
        return {
            "comparison_session": None,
            "basis": (
                "today versus yesterday, "
                "same milking session"
            ),
            "rows": [],
        }

    current_sessions = {
        str(
            getattr(
                row,
                "milking_session",
                "",
            )
            or ""
        ).upper()
        for row in today_rows
    }

    current_sessions.discard("")

    if not current_sessions:
        return {
            "comparison_session": None,
            "basis": (
                "today versus yesterday, "
                "same milking session"
            ),
            "rows": [],
        }

    session = max(
        current_sessions,
        key=lambda value: _SESSION_ORDER.get(
            value,
            0,
        ),
    )

    field = _SESSION_FIELDS.get(
        session,
        "total_yield",
    )

    current = {
        str(row.animal_id): float(
            getattr(row, field)
        )
        for row in today_rows
        if getattr(row, field, None) is not None
    }

    previous = {
        str(row.animal_id): float(
            getattr(row, field)
        )
        for row in yesterday_rows
        if getattr(row, field, None) is not None
    }

    rows = []

    for animal_id in sorted(
        set(current) | set(previous)
    ):
        current_value = current.get(animal_id)
        previous_value = previous.get(animal_id)
        change = _change_pct(
            current_value,
            previous_value,
        )

        rows.append(
            {
                "animal_id": animal_id,
                "today_liters": (
                    round(current_value, 3)
                    if current_value is not None
                    else None
                ),
                "previous_liters": (
                    round(previous_value, 3)
                    if previous_value is not None
                    else None
                ),
                "change_percent": change,
                "status": _drop_status(change),
            }
        )

    return {
        "comparison_session": session,
        "basis": (
            "today versus yesterday, "
            "same milking session"
        ),
        "rows": rows,
    }


@router.get("/production-summary")
def milk_production_summary(
    period: str = Query(default="7d"),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
):
    (
        start_date_value,
        end_date_exclusive,
        previous_start_date,
        previous_end_date,
        days,
    ) = _resolve_period(
        period,
        start_date,
        end_date,
    )

    start = datetime.combine(
        start_date_value,
        datetime.min.time(),
        tzinfo=timezone.utc,
    )

    end = datetime.combine(
        end_date_exclusive,
        datetime.min.time(),
        tzinfo=timezone.utc,
    )

    previous_start = datetime.combine(
        previous_start_date,
        datetime.min.time(),
        tzinfo=timezone.utc,
    )

    previous_end = datetime.combine(
        previous_end_date,
        datetime.min.time(),
        tzinfo=timezone.utc,
    )

    factory = RepositoryFactory.create()

    try:
        records = factory.milk().get_all()

        current_rows = _qualifying_rows(
            records,
            start,
            end,
        )

        previous_rows = _qualifying_rows(
            records,
            previous_start,
            previous_end,
        )

        current = _period_metrics(current_rows)
        previous = _period_metrics(previous_rows)

        today = datetime.now(
            timezone.utc
        ).date()

        yesterday = today - timedelta(days=1)

        today_start = datetime.combine(
            today,
            datetime.min.time(),
            tzinfo=timezone.utc,
        )

        tomorrow = today_start + timedelta(days=1)
        yesterday_start = today_start - timedelta(days=1)

        today_rows = _qualifying_rows(
            records,
            today_start,
            tomorrow,
        )

        yesterday_rows = _qualifying_rows(
            records,
            yesterday_start,
            today_start,
        )

        finding_service = OperationalFindingService(
            factory.operational_findings()
        )

        open_findings = [
            finding
            for finding in finding_service.list(
                module="MILK"
            )
            if finding.status != "RESOLVED"
        ]

        excluded_rows = sum(
            1
            for row in records
            if (
                _record_date(
                    row,
                    "production_date",
                    "recorded_at",
                )
                is not None
                and start
                <= _record_date(
                    row,
                    "production_date",
                    "recorded_at",
                )
                < end
                and (
                    not bool(
                        getattr(
                            row,
                            "session_ledger",
                            False,
                        )
                    )
                    or not _has_entered_yield(row)
                )
            )
        )

        return {
            "data_status": (
                "LIVE_PERSISTED_DATA"
                if current_rows
                else "NO_DATA"
            ),
            "period": {
                "key": period,
                "label": _PERIOD_LABELS[period],
                "start_date": (
                    start_date_value.isoformat()
                ),
                "end_date": (
                    end_exclusive
                    - timedelta(days=1)
                ).date().isoformat(),
                "days": days,
            },
            "kpis": {
                "total_production_liters": (
                    current["total_liters"]
                ),
                "average_per_day_liters": (
                    current["average_liters_per_day"]
                ),
                "average_per_cow_liters": (
                    current["average_liters_per_cow"]
                ),
                "morning_liters": (
                    current["morning_liters"]
                ),
                "evening_liters": (
                    current["evening_liters"]
                ),
                "open_drop_findings": len(
                    open_findings
                ),
            },
            "comparison": {
                "previous_period": {
                    "start_date": (
                        previous_start_date.isoformat()
                    ),
                    "end_date": (
                        previous_end
                        - timedelta(days=1)
                    ).isoformat(),
                    "days": days,
                    "data_status": (
                        "LIVE_PERSISTED_DATA"
                        if previous_rows
                        else "NO_DATA"
                    ),
                    "total_production_liters": (
                        previous["total_liters"]
                    ),
                    "average_per_day_liters": (
                        previous[
                            "average_liters_per_day"
                        ]
                    ),
                },
                "total_change_percent": _change_pct(
                    current["total_liters"],
                    previous["total_liters"],
                ),
                "average_per_day_change_percent": (
                    _change_pct(
                        current[
                            "average_liters_per_day"
                        ],
                        previous[
                            "average_liters_per_day"
                        ],
                    )
                ),
            },
            "trend": {
                "selector": "total",
                "available_series": [
                    "morning",
                    "afternoon",
                    "evening",
                    "total",
                ],
                "current": current["trend"],
                "previous": previous["trend"],
            },
            "production_by_animal": _same_session_table(
                today_rows,
                yesterday_rows,
            ),
            "drop_findings": [
                {
                    "finding_id": finding.finding_id,
                    "severity": finding.severity,
                    "title": finding.title,
                    "detail": finding.detail,
                    "status": finding.status,
                    "subject_id": finding.subject_id,
                    "route": finding.route,
                    "raised_at": (
                        finding.raised_at.isoformat()
                        if finding.raised_at
                        else None
                    ),
                }
                for finding in open_findings
            ],
            "coverage": {
                "observed_days": (
                    current["observed_days"]
                ),
                "animal_days_with_entered_yield": (
                    current[
                        "animal_days_with_entered_yield"
                    ]
                ),
                "excluded_rows": excluded_rows,
                "absence_policy": (
                    "Sessions not entered, NULL yields, "
                    "and pre-ledger rows are excluded; "
                    "absence is not treated as zero."
                ),
            },
            "methodology": {
                "source": (
                    "persisted MilkProduction repository "
                    "and OperationalFinding repository"
                ),
                "synthetic_values": False,
                "average_per_day_basis": (
                    "days with at least one entered "
                    "milk observation"
                ),
                "average_per_cow_basis": (
                    "animal-days with at least one "
                    "entered milk observation"
                ),
                "animal_comparison_basis": (
                    "today versus yesterday, "
                    "same milking session"
                ),
                "drop_thresholds": {
                    "red": (
                        "20% or greater decline"
                    ),
                    "amber": (
                        "10% to less than 20% decline"
                    ),
                    "good": (
                        "less than 10% decline"
                    ),
                },
            },
        }

    finally:
        factory.close()