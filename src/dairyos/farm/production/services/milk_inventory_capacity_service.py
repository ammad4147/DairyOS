from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime

from dairyos.data.repositories.repository_factory import RepositoryFactory


INACTIVE_STATUSES = frozenset({"VOID", "CANCELLED", "DELETED"})


def _as_date(value) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if hasattr(value, "date"):
        try:
            converted = value.date()
            return converted if isinstance(converted, date) else None
        except Exception:
            pass
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def _production_litres(row) -> float:
    value = getattr(row, "total_yield", None)
    if value is not None:
        return float(value or 0.0)
    return sum(
        float(item)
        for item in (
            getattr(row, "morning_yield", None),
            getattr(row, "afternoon_yield", None),
            getattr(row, "evening_yield", None),
        )
        if item is not None
    )


def overall_saleable_capacity(
    through_date: date,
    *,
    exclude_disposition_id: int | None = None,
    factory=None,
) -> dict[str, float]:
    """Return governed carried saleable milk through ``through_date``.

    Withdrawal production is retained as biological history but never enters
    the saleable pool. Ordinary dispositions consume only milk physically
    available on their date or carried from an earlier date. A historical
    orphan disposition therefore cannot create negative inventory debt that
    reduces milk produced later.
    """

    working_factory = factory or RepositoryFactory.create()
    owns_factory = factory is None

    try:
        production_rows = working_factory.milk().get_all() or []
        disposition_rows = working_factory.milk_dispositions().get_all() or []

        saleable_by_date: dict[date, float] = defaultdict(float)
        biological = 0.0
        withdrawal = 0.0

        for row in production_rows:
            row_date = _as_date(getattr(row, "production_date", None))
            if row_date is None or row_date > through_date:
                continue

            status = str(
                getattr(row, "status", "RECORDED") or "RECORDED"
            ).upper()
            if status in INACTIVE_STATUSES or status == "NOT_MILKED":
                continue

            litres = max(_production_litres(row), 0.0)
            biological += litres

            if status == "WITHDRAWAL":
                withdrawal += litres
            else:
                saleable_by_date[row_date] += litres

        ordinary_by_date: dict[date, float] = defaultdict(float)
        withdrawal_accounted = 0.0

        for row in disposition_rows:
            row_date = _as_date(getattr(row, "production_date", None))
            if row_date is None or row_date > through_date:
                continue
            if (
                exclude_disposition_id is not None
                and getattr(row, "id", None) == exclude_disposition_id
            ):
                continue

            status = str(
                getattr(row, "status", "RECORDED") or "RECORDED"
            ).upper()
            if status in INACTIVE_STATUSES:
                continue

            litres = max(
                float(getattr(row, "quantity_litres", 0.0) or 0.0),
                0.0,
            )
            disposition_type = str(
                getattr(row, "disposition_type", "") or ""
            ).upper()

            if disposition_type == "WITHDRAWAL":
                # Historical compatibility only. Withdrawal production is
                # already excluded from the saleable pool automatically.
                withdrawal_accounted += litres
            else:
                ordinary_by_date[row_date] += litres

        available = 0.0
        ordinary_accounted = 0.0
        unbacked_dispositions = 0.0

        dates = sorted(set(saleable_by_date) | set(ordinary_by_date))
        for operational_date in dates:
            available += saleable_by_date.get(operational_date, 0.0)

            requested = ordinary_by_date.get(operational_date, 0.0)
            applied = min(requested, available)
            ordinary_accounted += applied
            unbacked_dispositions += max(requested - applied, 0.0)
            available -= applied

        saleable = max(biological - withdrawal, 0.0)

        return {
            "biological_production_litres": round(biological, 3),
            "withdrawal_litres": round(withdrawal, 3),
            "saleable_production_litres": round(saleable, 3),
            "ordinary_accounted_litres": round(ordinary_accounted, 3),
            "withdrawal_accounted_litres": round(withdrawal_accounted, 3),
            "unbacked_disposition_litres": round(unbacked_dispositions, 3),
            "available_saleable_litres": round(max(available, 0.0), 3),
        }
    finally:
        if owns_factory:
            working_factory.close()
