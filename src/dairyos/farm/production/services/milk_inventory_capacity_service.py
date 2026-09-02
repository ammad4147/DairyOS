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
    """Return the governed carried milk balance through ``through_date``.

    All physically produced milk enters recorded production. Milk produced
    during a treatment-withdrawal period is removed from the saleable balance
    by an automatic WASTAGE disposition at entry time. Historical rows that
    were stored with status WITHDRAWAL before that rule existed are treated as
    implicit wastage for compatibility, without deleting or rewriting them.

    Dispositions are applied chronologically and can consume only milk that
    physically exists by their date. An orphan historical disposition cannot
    create negative inventory debt against future production.
    """

    working_factory = factory or RepositoryFactory.create()
    owns_factory = factory is None

    try:
        production_rows = working_factory.milk().get_all() or []
        disposition_rows = working_factory.milk_dispositions().get_all() or []

        production_by_date: dict[date, float] = defaultdict(float)
        legacy_withdrawal_by_date: dict[date, float] = defaultdict(float)
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
            production_by_date[row_date] += litres

            if status == "WITHDRAWAL":
                withdrawal += litres
                legacy_withdrawal_by_date[row_date] += litres

        disposition_by_date: dict[date, float] = defaultdict(float)
        explicit_withdrawal_by_date: dict[date, float] = defaultdict(float)

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
            disposition_by_date[row_date] += litres

            if str(
                getattr(row, "disposition_type", "") or ""
            ).upper() == "WITHDRAWAL":
                explicit_withdrawal_by_date[row_date] += litres

        # Compatibility for historical data created before withdrawal milk
        # was automatically posted to WASTAGE. Do not double-count an old
        # explicit WITHDRAWAL disposition if one already represents it.
        legacy_implicit_wastage_by_date: dict[date, float] = defaultdict(float)
        for operational_date, litres in legacy_withdrawal_by_date.items():
            legacy_implicit_wastage_by_date[operational_date] = max(
                litres - explicit_withdrawal_by_date.get(operational_date, 0.0),
                0.0,
            )

        available = 0.0
        accounted = 0.0
        unbacked_dispositions = 0.0
        legacy_implicit_wastage = 0.0

        dates = sorted(
            set(production_by_date)
            | set(disposition_by_date)
            | set(legacy_implicit_wastage_by_date)
        )

        for operational_date in dates:
            available += production_by_date.get(operational_date, 0.0)

            requested = (
                disposition_by_date.get(operational_date, 0.0)
                + legacy_implicit_wastage_by_date.get(operational_date, 0.0)
            )
            legacy_implicit_wastage += legacy_implicit_wastage_by_date.get(
                operational_date, 0.0
            )

            applied = min(requested, available)
            accounted += applied
            unbacked_dispositions += max(requested - applied, 0.0)
            available -= applied

        return {
            "biological_production_litres": round(biological, 3),
            "recorded_production_litres": round(biological, 3),
            "withdrawal_litres": round(withdrawal, 3),
            "saleable_production_litres": round(biological, 3),
            "ordinary_accounted_litres": round(accounted, 3),
            "legacy_implicit_wastage_litres": round(
                legacy_implicit_wastage, 3
            ),
            "unbacked_disposition_litres": round(unbacked_dispositions, 3),
            "available_saleable_litres": round(max(available, 0.0), 3),
        }
    finally:
        if owns_factory:
            working_factory.close()
