from __future__ import annotations

from datetime import date

from dairyos.data.repositories.repository_factory import RepositoryFactory


INACTIVE_STATUSES = frozenset({"VOID", "CANCELLED", "DELETED"})


def _as_date(value) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if hasattr(value, "date"):
        try:
            return value.date()
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
    """Return the cumulative governed milk balance available through a date.

    Milk is a carried physical inventory. A sale or ordinary disposition on a
    given date may therefore consume saleable milk produced on earlier dates,
    provided that milk has not already been disposed of. Withdrawal milk is
    excluded from the saleable pool and is never allowed to subsidise an
    ordinary disposition.
    """

    working_factory = factory or RepositoryFactory.create()
    owns_factory = factory is None

    try:
        production_rows = working_factory.milk().get_all() or []
        disposition_rows = working_factory.milk_dispositions().get_all() or []

        biological = 0.0
        withdrawal = 0.0

        for row in production_rows:
            row_date = _as_date(getattr(row, "production_date", None))
            if row_date is None or row_date > through_date:
                continue
            status = str(getattr(row, "status", "RECORDED") or "RECORDED").upper()
            if status in INACTIVE_STATUSES or status == "NOT_MILKED":
                continue
            litres = _production_litres(row)
            biological += litres
            if status == "WITHDRAWAL":
                withdrawal += litres

        ordinary_accounted = 0.0
        withdrawal_accounted = 0.0

        for row in disposition_rows:
            row_date = _as_date(getattr(row, "production_date", None))
            if row_date is None or row_date > through_date:
                continue
            if exclude_disposition_id is not None and getattr(row, "id", None) == exclude_disposition_id:
                continue
            status = str(getattr(row, "status", "RECORDED") or "RECORDED").upper()
            if status in INACTIVE_STATUSES:
                continue
            litres = float(getattr(row, "quantity_litres", 0.0) or 0.0)
            if str(getattr(row, "disposition_type", "") or "").upper() == "WITHDRAWAL":
                withdrawal_accounted += litres
            else:
                ordinary_accounted += litres

        saleable = max(biological - withdrawal, 0.0)
        available = max(saleable - ordinary_accounted, 0.0)

        return {
            "biological_production_litres": round(biological, 3),
            "withdrawal_litres": round(withdrawal, 3),
            "saleable_production_litres": round(saleable, 3),
            "ordinary_accounted_litres": round(ordinary_accounted, 3),
            "withdrawal_accounted_litres": round(withdrawal_accounted, 3),
            "available_saleable_litres": round(available, 3),
        }
    finally:
        if owns_factory:
            working_factory.close()
