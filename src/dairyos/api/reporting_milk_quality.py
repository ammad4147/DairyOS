"""Authoritative Milk Quality projections for governed Reporting.

Reporting consumes the existing MilkQualityRepository persistence authority.
It preserves recorded samples and revision history and mirrors the established
quality-summary arithmetic without creating a second quality ledger.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any

from fastapi import HTTPException


def _scalar(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return "; ".join(f"{key}={_scalar(value[key])}" for key in sorted(value))
    if isinstance(value, (list, tuple)):
        return " | ".join(str(_scalar(item)) for item in value)
    return str(value)


def _sample_row(row: Any) -> dict[str, Any]:
    quality_date = getattr(row, "quality_date", None)
    if isinstance(quality_date, datetime):
        quality_date = quality_date.date()
    return {
        "id": getattr(row, "id", None),
        "quality_date": quality_date.isoformat() if isinstance(quality_date, date) else _scalar(quality_date),
        "fat_pct": _scalar(getattr(row, "fat_pct", None)),
        "snf_pct": _scalar(getattr(row, "snf_pct", None)),
        "sample_type": getattr(row, "sample_type", None),
        "notes": getattr(row, "notes", None),
        "recorded_by": getattr(row, "recorded_by", None),
        "status": getattr(row, "status", None),
        "recorded_at": _scalar(getattr(row, "recorded_at", None)),
        "updated_at": _scalar(getattr(row, "updated_at", None)),
        "revision_history": _scalar(getattr(row, "revision_history", None) or []),
        "somatic_cell_count": _scalar(getattr(row, "somatic_cell_count", None)),
        "antibiotic_residue_status": _scalar(getattr(row, "antibiotic_residue_status", None)),
        "cooling_chain_break": _scalar(getattr(row, "cooling_chain_break", None)),
        "adulteration_test_result": _scalar(getattr(row, "adulteration_test_result", None)),
        "iso_17025_ref": _scalar(getattr(row, "iso_17025_ref", None)),
        "analyst_id": _scalar(getattr(row, "analyst_id", None)),
    }


def _period(payload: Any, operational_today: date) -> tuple[date, date]:
    mode = str(payload.period_mode)
    if mode == "OPERATIONAL_DATE":
        return payload.operational_date, payload.operational_date
    if mode in {"DATE_RANGE", "CUSTOM_PERIOD"}:
        return payload.start_date, payload.end_date
    if mode == "MONTH":
        selected = payload.as_of_date or payload.operational_date or operational_today
        start = selected.replace(day=1)
        next_month = date(selected.year + 1, 1, 1) if selected.month == 12 else date(selected.year, selected.month + 1, 1)
        return start, next_month - timedelta(days=1)
    raise HTTPException(status_code=422, detail="Unsupported Milk Quality Reporting period mode.")


def _repository(container: Any):
    factory = getattr(container, "repository_factory", None)
    getter = getattr(factory, "milk_quality", None) if factory is not None else None
    if not callable(getter):
        raise HTTPException(
            status_code=503,
            detail={
                "code": "REPORTING_AUTHORITY_UNAVAILABLE",
                "authority": "MilkQuality",
                "message": "Authoritative Milk Quality repository is unavailable for Reporting.",
            },
        )
    repository = getter()
    if repository is None or not callable(getattr(repository, "get_range", None)):
        raise HTTPException(
            status_code=503,
            detail={
                "code": "REPORTING_AUTHORITY_UNAVAILABLE",
                "authority": "MilkQuality",
                "message": "Authoritative Milk Quality range authority is unavailable for Reporting.",
            },
        )
    return repository


def milk_quality_reporting_dataset(payload: Any, container: Any, operational_today: date) -> dict[str, Any]:
    repository = _repository(container)
    start, end = _period(payload, operational_today)
    records = list(repository.get_range(start, end) or [])

    sample_type = payload.filters.get("sample_type")
    status = payload.filters.get("status")
    selected = []
    for row in records:
        if sample_type not in (None, "", "ALL") and str(getattr(row, "sample_type", "")).upper() != str(sample_type).strip().upper():
            continue
        if status not in (None, "", "ALL") and str(getattr(row, "status", "")).upper() != str(status).strip().upper():
            continue
        try:
            scc_breach = getattr(row, "somatic_cell_count", None) is not None and float(getattr(row, "somatic_cell_count")) > 400000
        except (TypeError, ValueError):
            scc_breach = False
        checks = {"scc_alert": scc_breach, "antibiotic_flag": str(getattr(row, "antibiotic_residue_status", "")).upper() in {"POSITIVE", "PRESENT", "FLAGGED"}, "temp_breach": bool(getattr(row, "cooling_chain_break", False)), "adulteration_suspect": str(getattr(row, "adulteration_test_result", "")).upper() in {"SUSPECT", "POSITIVE", "FLAGGED"}}
        threshold = payload.filters.get("milk_quality_threshold")
        if threshold not in (None, "", "ALL") and not checks.get(str(threshold).strip().lower(), False): continue
        for key, expected in checks.items():
            wanted = payload.filters.get(key)
            if wanted not in (None, "", "ALL") and expected != (str(wanted).upper() in {"TRUE", "YES", "1", "SCC_ALERT", "ANTIBIOTIC_FLAG", "TEMP_BREACH", "ADULTERATION_SUSPECT"}): continue
        selected.append(row)

    sample_count = len(selected)
    average_fat = round(sum(float(row.fat_pct) for row in selected) / sample_count, 3) if sample_count else None
    average_snf = round(sum(float(row.snf_pct) for row in selected) / sample_count, 3) if sample_count else None
    latest = max(selected, key=lambda row: getattr(row, "quality_date")) if selected else None

    summary = {
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "sample_count": sample_count,
        "average_fat_pct": average_fat,
        "average_snf_pct": average_snf,
        "latest_sample_date": _sample_row(latest)["quality_date"] if latest is not None else None,
        "revision_history_preserved": True,
    }
    rows = [_sample_row(row) for row in selected]
    if payload.report_id == "quality-summary":
        rows = [
            {"metric": "sample_count", "value": sample_count},
            {"metric": "average_fat_pct", "value": average_fat},
            {"metric": "average_snf_pct", "value": average_snf},
            {"metric": "latest_sample_date", "value": summary["latest_sample_date"]},
        ]

    columns: list[str] = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    return {
        "dataset_status": "AUTHORITATIVE_DATASET",
        "authority_status": "AUTHORITY_AVAILABLE",
        "columns": columns,
        "rows": rows,
        "summary": summary,
        "warnings": [] if selected else ["No recorded Milk Quality samples match the selected period and filters."],
    }
