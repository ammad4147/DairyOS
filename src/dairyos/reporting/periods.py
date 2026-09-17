"""Reporting period resolution.

Every period is an inclusive ``[start, end]`` pair of farm operational dates.
"Today" always comes from ``OperationalDateAuthority`` (the farm clock), never
from UTC and never from the browser.

DairyOS has no configurable financial year. Quarters are therefore calendar
quarters and "Year to Date" / "Calendar Year" follow the calendar year. If a
governed financial-year setting is ever introduced, this is the single place
that must consume it.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

PERIOD_MODES = (
    "TODAY",
    "YESTERDAY",
    "LAST_7_DAYS",
    "LAST_30_DAYS",
    "CURRENT_MONTH",
    "PREVIOUS_MONTH",
    "CURRENT_QUARTER",
    "PREVIOUS_QUARTER",
    "YEAR_TO_DATE",
    "CALENDAR_YEAR",
    "MONTH",
    "QUARTER",
    "CUSTOM",
)

PERIOD_MODE_LABELS = {
    "TODAY": "Today",
    "YESTERDAY": "Yesterday",
    "LAST_7_DAYS": "Last 7 Days",
    "LAST_30_DAYS": "Last 30 Days",
    "CURRENT_MONTH": "Current Month",
    "PREVIOUS_MONTH": "Previous Month",
    "CURRENT_QUARTER": "Current Quarter",
    "PREVIOUS_QUARTER": "Previous Quarter",
    "YEAR_TO_DATE": "Year to Date",
    "CALENDAR_YEAR": "Calendar Year",
    "MONTH": "Monthly",
    "QUARTER": "Quarterly",
    "CUSTOM": "Custom Date Range",
}

QUARTER_LABELS = {
    1: "Q1 (January to March)",
    2: "Q2 (April to June)",
    3: "Q3 (July to September)",
    4: "Q4 (October to December)",
}


class PeriodError(ValueError):
    """The requested period is not valid."""


@dataclass(frozen=True)
class ResolvedPeriod:
    kind: str
    mode: str | None
    start: date | None
    end: date | None
    label: str
    operational_today: date

    @property
    def as_of(self) -> date:
        return self.end or self.operational_today

    @property
    def days(self) -> int:
        if self.start is None or self.end is None:
            return 0
        return (self.end - self.start).days + 1

    def contains(self, value: date | None) -> bool:
        if value is None:
            return False
        if self.start is not None and value < self.start:
            return False
        if self.end is not None and value > self.end:
            return False
        return True

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "mode": self.mode,
            "start_date": self.start.isoformat() if self.start else None,
            "end_date": self.end.isoformat() if self.end else None,
            "as_of_date": self.as_of.isoformat(),
            "label": self.label,
            "days": self.days,
            "operational_today": self.operational_today.isoformat(),
        }


def format_date(value: date) -> str:
    """DairyOS report date presentation, for example ``01-Sep-2026``."""
    return value.strftime("%d-%b-%Y")


def month_bounds(year: int, month: int) -> tuple[date, date]:
    if not 1 <= month <= 12:
        raise PeriodError("Month must be between 1 and 12.")
    return date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])


def quarter_bounds(year: int, quarter: int) -> tuple[date, date]:
    if quarter not in (1, 2, 3, 4):
        raise PeriodError("Quarter must be 1, 2, 3 or 4.")
    first_month = (quarter - 1) * 3 + 1
    return month_bounds(year, first_month)[0], month_bounds(year, first_month + 2)[1]


def quarter_of(value: date) -> int:
    return (value.month - 1) // 3 + 1


def _parse_date(value: Any, name: str) -> date:
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError) as exc:
        raise PeriodError(f"{name} must be a valid date.") from exc


def _parse_year(value: Any) -> int:
    try:
        year = int(value)
    except (TypeError, ValueError) as exc:
        raise PeriodError("Year must be a whole number.") from exc
    if not 1990 <= year <= 2200:
        raise PeriodError("Year is outside the supported range.")
    return year


def _range_label(start: date, end: date) -> str:
    if start == end:
        return format_date(start)
    return f"{format_date(start)} to {format_date(end)}"


def resolve_period(
    kind: str,
    spec: dict[str, Any] | None,
    *,
    operational_today: date,
    default_mode: str = "CURRENT_MONTH",
) -> ResolvedPeriod:
    """Resolve a request period specification for one report.

    ``kind`` is the report's period kind (``none``, ``as_of`` or ``range``).
    """
    spec = dict(spec or {})
    today = operational_today

    if kind == "none":
        return ResolvedPeriod("none", None, None, today, f"Current as of {format_date(today)}", today)

    if kind == "as_of":
        raw = spec.get("as_of_date")
        selected = _parse_date(raw, "As of Date") if raw else today
        return ResolvedPeriod("as_of", "AS_OF", None, selected, f"As of {format_date(selected)}", today)

    if kind != "range":
        raise PeriodError("Unsupported report period kind.")

    mode = str(spec.get("mode") or default_mode).strip().upper()
    if mode not in PERIOD_MODES:
        raise PeriodError("Unsupported reporting period.")

    if mode == "TODAY":
        start = end = today
    elif mode == "YESTERDAY":
        start = end = today - timedelta(days=1)
    elif mode == "LAST_7_DAYS":
        start, end = today - timedelta(days=6), today
    elif mode == "LAST_30_DAYS":
        start, end = today - timedelta(days=29), today
    elif mode == "CURRENT_MONTH":
        start, end = month_bounds(today.year, today.month)
    elif mode == "PREVIOUS_MONTH":
        last = today.replace(day=1) - timedelta(days=1)
        start, end = month_bounds(last.year, last.month)
    elif mode == "CURRENT_QUARTER":
        start, end = quarter_bounds(today.year, quarter_of(today))
    elif mode == "PREVIOUS_QUARTER":
        quarter = quarter_of(today) - 1
        year = today.year
        if quarter == 0:
            quarter, year = 4, year - 1
        start, end = quarter_bounds(year, quarter)
    elif mode == "YEAR_TO_DATE":
        start, end = date(today.year, 1, 1), today
    elif mode == "CALENDAR_YEAR":
        year = _parse_year(spec.get("year") or today.year)
        start, end = date(year, 1, 1), date(year, 12, 31)
    elif mode == "MONTH":
        year = _parse_year(spec.get("year") or today.year)
        try:
            month = int(spec.get("month") or today.month)
        except (TypeError, ValueError) as exc:
            raise PeriodError("Month must be between 1 and 12.") from exc
        start, end = month_bounds(year, month)
    elif mode == "QUARTER":
        year = _parse_year(spec.get("year") or today.year)
        try:
            quarter = int(spec.get("quarter") or quarter_of(today))
        except (TypeError, ValueError) as exc:
            raise PeriodError("Quarter must be 1, 2, 3 or 4.") from exc
        start, end = quarter_bounds(year, quarter)
    else:  # CUSTOM
        if not spec.get("start_date") or not spec.get("end_date"):
            raise PeriodError("From Date and To Date are both required.")
        start = _parse_date(spec.get("start_date"), "From Date")
        end = _parse_date(spec.get("end_date"), "To Date")
        if start > end:
            raise PeriodError("From Date must be on or before To Date.")

    if mode == "MONTH":
        label = f"{start.strftime('%B %Y')} ({_range_label(start, end)})"
    elif mode == "QUARTER":
        label = f"Q{quarter_of(start)} {start.year} ({_range_label(start, end)})"
    elif mode == "CUSTOM":
        label = _range_label(start, end)
    else:
        label = f"{PERIOD_MODE_LABELS[mode]} ({_range_label(start, end)})"

    return ResolvedPeriod("range", mode, start, end, label, today)


def month_sequence(start: date, end: date) -> list[tuple[date, date]]:
    """Calendar months overlapping ``[start, end]``, clipped to the range."""
    months: list[tuple[date, date]] = []
    cursor = start.replace(day=1)
    while cursor <= end:
        first, last = month_bounds(cursor.year, cursor.month)
        months.append((max(first, start), min(last, end)))
        cursor = last + timedelta(days=1)
    return months


def quarter_sequence(start: date, end: date) -> list[tuple[date, date]]:
    quarters: list[tuple[date, date]] = []
    first, last = quarter_bounds(start.year, quarter_of(start))
    while first <= end:
        quarters.append((max(first, start), min(last, end)))
        nxt = last + timedelta(days=1)
        first, last = quarter_bounds(nxt.year, quarter_of(nxt))
    return quarters
