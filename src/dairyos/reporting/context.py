"""Read context and small shared helpers for report builders."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from dairyos.reporting.definitions import ReportDefinition
from dairyos.reporting.periods import ResolvedPeriod

MONEY_QUANTUM = Decimal("0.01")
ZERO = Decimal("0.00")


class ReportParameterError(ValueError):
    """An operator-supplied report parameter is not valid."""


def money(value: Any) -> Decimal:
    """Fixed-point currency amount. Reporting never sums money as float."""
    if value is None or value == "":
        return ZERO
    return Decimal(str(value)).quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


def to_date(value: Any) -> date | None:
    """Calendar date of a persisted DairyOS value.

    DairyOS persists dated facts either as ``Date`` or as a ``DateTime``
    whose date part is the operator-selected farm date. Reporting follows the
    same convention as the operational tabs (the date part of the stored
    value) so a report never disagrees with its source screen.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def upper(value: Any) -> str:
    return str(value or "").strip().upper()


def ratio(numerator: Any, denominator: Any, places: int = 2) -> float | None:
    """Safe division. A zero or missing denominator yields ``None`` (shown
    as not available), never a fabricated zero."""
    try:
        bottom = float(denominator or 0)
        if bottom == 0:
            return None
        return round(float(numerator or 0) / bottom, places)
    except (TypeError, ValueError):
        return None


def age_label(born: date | None, as_of: date) -> str | None:
    if born is None or born > as_of:
        return None
    months = (as_of.year - born.year) * 12 + as_of.month - born.month
    if as_of.day < born.day:
        months -= 1
    if months < 1:
        return f"{(as_of - born).days} d"
    years, rest = divmod(months, 12)
    if years == 0:
        return f"{rest} mo"
    return f"{years} y {rest} mo" if rest else f"{years} y"


def age_months(born: date | None, as_of: date) -> int | None:
    if born is None or born > as_of:
        return None
    months = (as_of.year - born.year) * 12 + as_of.month - born.month
    return months - 1 if as_of.day < born.day else months


@dataclass
class ReportContext:
    definition: ReportDefinition
    container: Any
    factory: Any
    period: ResolvedPeriod
    filters: dict[str, Any]
    today: date
    generated_at: datetime
    _cache: dict[str, Any] = field(default_factory=dict)

    @property
    def session(self):
        return self.factory.session

    @property
    def preset(self) -> dict[str, Any]:
        return self.definition.preset

    def filter(self, key: str) -> str | None:
        value = self.filters.get(key)
        if value is None or isinstance(value, bool):
            return None
        text = str(value).strip()
        if not text or text.upper() == "ALL":
            return None
        return text

    def flag(self, key: str, default: bool = False) -> bool:
        value = self.filters.get(key, default)
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "on"}

    def cached(self, key: str, loader):
        if key not in self._cache:
            self._cache[key] = loader()
        return self._cache[key]

    def animals(self) -> list[Any]:
        return self.cached("animals", lambda: list(self.factory.animal().get_all() or []))

    def animal_index(self) -> dict[str, Any]:
        return self.cached(
            "animal_index",
            lambda: {str(a.animal_id): a for a in self.animals()},
        )
