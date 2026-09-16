"""Authoritative Milk projections for governed Reporting.

Reporting consumes the existing Milk production, correction, disposition, and
reconciliation authorities. It does not create a competing Milk ledger.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any

from fastapi import HTTPException

from dairyos.farm.herd.services.animal_milking_schedule_service import (
    AnimalMilkingScheduleService,
)
from dairyos.farm.production.services.milk_reconciliation_service import (
    MilkReconciliationService,
)


SESSION_FIELDS = {
    "MORNING": "morning_yield",
    "AFTERNOON": "afternoon_yield",
    "EVENING": "evening_yield",
}
ACTIVE_PRODUCTION_STATUSES_EXCLUDED = {"VOID", "NOT_MILKED"}


def _plain_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def _scalar(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, (dict, list, tuple, set)):
        return str(value)
    return str(value)


def _row(record: Any) -> dict[str, Any]:
    values = record if isinstance(record, dict) else vars(record) if hasattr(record, "__dict__") else {}
    return {
        str(key): _scalar(value)
        for key, value in values.items()
        if not str(key).startswith("_")
    }


def _dataset(
    rows: list[dict[str, Any]],
    *,
    summary: dict[str, Any],
    status: str = "AUTHORITATIVE_DATASET",
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    columns: list[str] = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    return {
        "dataset_status": status,
        "authority_status": "AUTHORITY_AVAILABLE",
        "columns": columns,
        "rows": rows,
        "summary": summary,
        "warnings": warnings or [],
    }


def _period(payload: Any, operational_today: date) -> tuple[date, date]:
    mode = str(payload.period_mode)
    if mode == "TODAY":
        return operational_today, operational_today
    if mode == "YESTERDAY":
        selected = operational_today - timedelta(days=1)
        return selected, selected
    if mode == "OPERATIONAL_DATE":
        return payload.operational_date, payload.operational_date
    if mode in {"DATE_RANGE", "CUSTOM_PERIOD"}:
        return payload.start_date, payload.end_date
    if mode == "MONTH":
        selected = payload.as_of_date or payload.operational_date or operational_today
        start = selected.replace(day=1)
        next_month = date(selected.year + 1, 1, 1) if selected.month == 12 else date(selected.year, selected.month + 1, 1)
        return start, next_month - timedelta(days=1)
    raise HTTPException(status_code=422, detail="Unsupported Milk Reporting period mode.")


def _factory(container: Any):
    factory = getattr(container, "repository_factory", None)
    if factory is None:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "REPORTING_AUTHORITY_UNAVAILABLE",
                "authority": "Milk",
                "message": "Authoritative repository factory is unavailable for Milk Reporting.",
            },
        )
    return factory


def _production_date(record: Any) -> date | None:
    return _plain_date(getattr(record, "production_date", None))


def _active_production(record: Any) -> bool:
    return (
        bool(getattr(record, "session_ledger", False))
        and str(getattr(record, "status", "RECORDED") or "RECORDED").upper()
        not in ACTIVE_PRODUCTION_STATUSES_EXCLUDED
    )


def _schedule_frequency(factory: Any, animal_id: str, production_day: date) -> str | None:
    animal_repository = factory.animal()
    animal = animal_repository.get_by_animal_id(str(animal_id))
    if animal is None:
        return None
    return AnimalMilkingScheduleService(animal_repository).get_frequency_for_date(
        animal,
        production_day,
    )


def _correction_repository(factory: Any, *, required: bool) -> Any | None:
    getter = getattr(factory, "milk_corrections", None)
    if callable(getter):
        repository = getter()
        if repository is not None and callable(getattr(repository, "get_for_production", None)):
            return repository
    if required:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "REPORTING_AUTHORITY_UNAVAILABLE",
                "authority": "MilkCorrections",
                "message": "Milk correction authority is required when Milk production records are present.",
            },
        )
    return None


def _production_rows(payload: Any, container: Any, operational_today: date) -> dict[str, Any]:
    factory = _factory(container)
    production_repository = factory.milk()
    start, end = _period(payload, operational_today)

    session = str(payload.filters.get("session") or "ALL").strip().upper()
    if session not in {"ALL", *SESSION_FIELDS}:
        raise HTTPException(status_code=422, detail="Milk Reporting session must be MORNING, AFTERNOON, EVENING, or ALL.")

    animal_filter = payload.filters.get("animal_id")
    cohort_filter = payload.filters.get("milking_cohort")
    category_filter = payload.filters.get("category")
    if category_filter not in (None, "", "ALL"):
        raise HTTPException(
            status_code=422,
            detail="Historical Milk category filtering is not yet backed by an effective-dated category authority; no current-state category has been substituted.",
        )

    records = sorted(
        list(production_repository.get_all() or []),
        key=lambda item: (_production_date(item) or date.min, str(getattr(item, "animal_id", "")), int(getattr(item, "id", 0) or 0)),
    )
    selected_records = [
        record
        for record in records
        if (
            (production_day := _production_date(record)) is not None
            and start <= production_day <= end
            and (animal_filter is None or str(getattr(record, "animal_id", "")) == str(animal_filter))
        )
    ]
    correction_repository = _correction_repository(factory, required=bool(selected_records))

    rows: list[dict[str, Any]] = []
    active_litres = 0.0
    active_records = 0
    correction_count = 0

    for record in selected_records:
        production_day = _production_date(record)
        if production_day is None:
            continue

        frequency = _schedule_frequency(factory, str(getattr(record, "animal_id", "")), production_day)
        if cohort_filter not in (None, "", "ALL") and str(frequency or "").upper() != str(cohort_filter).strip().upper():
            continue

        data = _row(record)
        data["row_type"] = "PRODUCTION"
        data["operational_date"] = production_day.isoformat()
        data["milking_cohort"] = frequency

        if session in SESSION_FIELDS:
            field = SESSION_FIELDS[session]
            selected_value = getattr(record, field, None)
            data = {
                "row_type": "PRODUCTION",
                "id": getattr(record, "id", None),
                "animal_id": getattr(record, "animal_id", None),
                "operational_date": production_day.isoformat(),
                "session": session,
                "session_yield_litres": _scalar(selected_value),
                "milking_cohort": frequency,
                "status": getattr(record, "status", None),
                "session_ledger": bool(getattr(record, "session_ledger", False)),
                "recorded_at": _scalar(getattr(record, "recorded_at", None)),
                "notes": getattr(record, "notes", None),
            }

        rows.append(data)

        if _active_production(record):
            if session in SESSION_FIELDS:
                value = getattr(record, SESSION_FIELDS[session], None)
            else:
                value = getattr(record, "total_yield", None)
                if value is None:
                    value = sum(
                        float(getattr(record, field))
                        for field in SESSION_FIELDS.values()
                        if getattr(record, field, None) is not None
                    )
            if value is not None:
                active_litres += float(value)
            active_records += 1

        production_id = getattr(record, "id", None)
        if production_id is not None and correction_repository is not None:
            for correction in list(correction_repository.get_for_production(production_id) or []):
                correction_count += 1
                correction_row = _row(correction)
                correction_row["row_type"] = "CORRECTION"
                correction_row["animal_id"] = getattr(record, "animal_id", None)
                correction_row["operational_date"] = production_day.isoformat()
                rows.append(correction_row)

    return _dataset(
        rows,
        summary={
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "session": session,
            "active_milk_liters": round(active_litres, 3),
            "active_production_records": active_records,
            "correction_records": correction_count,
            "void_excluded_from_active_totals": True,
            "not_milked_excluded_from_active_totals": True,
        },
        warnings=[] if rows else ["No Milk production records match the selected period and filters."],
    )


def _date_range(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def _disposition_rows(payload: Any, container: Any, operational_today: date) -> dict[str, Any]:
    factory = _factory(container)
    production_repository = factory.milk()
    disposition_repository = factory.milk_dispositions()
    start, end = _period(payload, operational_today)
    wanted_type = payload.filters.get("disposition_type")
    wanted_status = payload.filters.get("status")

    reconciliation = MilkReconciliationService(
        disposition_repository=disposition_repository,
        production_repository=production_repository,
    )

    rows: list[dict[str, Any]] = []
    reconciliation_statuses: dict[str, int] = {}
    produced_litres = 0.0
    accounted_litres = 0.0
    unaccounted_litres = 0.0
    over_accounted_litres = 0.0

    for selected in _date_range(start, end):
        result = reconciliation.reconcile(selected, raise_finding=False)
        status = str(result.get("status") or "UNKNOWN")
        reconciliation_statuses[status] = reconciliation_statuses.get(status, 0) + 1
        for key, target in (
            ("produced_litres", "produced"),
            ("accounted_litres", "accounted"),
            ("unaccounted_litres", "unaccounted"),
            ("over_accounted_litres", "over_accounted"),
        ):
            value = result.get(key)
            if value is None:
                continue
            if target == "produced":
                produced_litres += float(value)
            elif target == "accounted":
                accounted_litres += float(value)
            elif target == "unaccounted":
                unaccounted_litres += float(value)
            else:
                over_accounted_litres += float(value)

        rows.append(
            {
                "row_type": "RECONCILIATION",
                "production_date": selected.isoformat(),
                "production_complete": result.get("production_complete"),
                "produced_litres": result.get("produced_litres"),
                "saleable_litres": result.get("saleable_litres"),
                "withdrawal_litres": result.get("withdrawal_litres"),
                "accounted_litres": result.get("accounted_litres"),
                "sold_litres": result.get("sold_litres"),
                "non_sale_accounted_litres": result.get("non_sale_accounted_litres"),
                "unaccounted_litres": result.get("unaccounted_litres"),
                "over_accounted_litres": result.get("over_accounted_litres"),
                "sale_value": result.get("sale_value"),
                "cash_received": result.get("cash_received"),
                "receivable_outstanding": result.get("receivable_outstanding"),
                "reconciliation_status": status,
            }
        )

        for disposition in list(disposition_repository.get_by_date(selected) or []):
            disposition_type = str(getattr(disposition, "disposition_type", "") or "").upper()
            disposition_status = str(getattr(disposition, "status", "RECORDED") or "RECORDED").upper()
            if wanted_type not in (None, "", "ALL") and disposition_type != str(wanted_type).strip().upper():
                continue
            if wanted_status not in (None, "", "ALL") and disposition_status != str(wanted_status).strip().upper():
                continue
            data = _row(disposition)
            data["row_type"] = "DISPOSITION"
            rows.append(data)

    return _dataset(
        rows,
        summary={
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "produced_litres": round(produced_litres, 3),
            "accounted_litres": round(accounted_litres, 3),
            "unaccounted_litres": round(unaccounted_litres, 3),
            "over_accounted_litres": round(over_accounted_litres, 3),
            "reconciliation_statuses": str(dict(sorted(reconciliation_statuses.items()))),
            "void_rows_retained_for_audit": True,
            "void_excluded_by_reconciliation_authority": True,
        },
        warnings=[] if rows else ["No Milk reconciliation or disposition records match the selected period."],
    )


def milk_reporting_dataset(payload: Any, container: Any, operational_today: date) -> dict[str, Any]:
    """Dispatch Milk Reporting to established DairyOS authorities."""
    if payload.report_id in {"daily-milk", "milk-animal"}:
        return _production_rows(payload, container, operational_today)
    if payload.report_id == "milk-disposition":
        return _disposition_rows(payload, container, operational_today)
    raise HTTPException(status_code=422, detail="Unsupported Milk Reporting report_id.")
