"""Reporting presentation adapter for the authoritative lifetime Animal Passport.

This module does not calculate animal history or biological state.  It consumes
``DatabaseAwareLifetimeAnimalPassportService`` and only flattens its canonical
read model for Reporting preview/export surfaces.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from fastapi import HTTPException

from dairyos.application.database_aware_animal_passport import (
    DatabaseAwareLifetimeAnimalPassportService,
)


def _scalar(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)


def _timeline_record(record: Any) -> str | None:
    """Preserve a canonical event payload as deterministic export-safe text."""
    if record is None:
        return None
    if not isinstance(record, dict):
        return str(record)

    parts: list[str] = []
    for key in sorted(record):
        value = record[key]
        if value is None:
            continue
        if isinstance(value, dict):
            value = ", ".join(
                f"{nested_key}={_scalar(nested_value)}"
                for nested_key, nested_value in sorted(value.items())
                if nested_value is not None
            )
        elif isinstance(value, (list, tuple, set)):
            value = ", ".join(str(_scalar(item)) for item in value)
        else:
            value = _scalar(value)
        parts.append(f"{key}={value}")
    return "; ".join(parts)


def animal_passport_dataset(
    payload: Any,
    container: Any,
    operational_today: date,
) -> dict[str, Any]:
    """Consume the canonical Passport and shape it for Reporting only."""
    raw_animal_id = payload.filters.get("animal_id")
    animal_id = str(raw_animal_id).strip() if raw_animal_id is not None else ""
    if not animal_id:
        raise HTTPException(
            status_code=422,
            detail="animal_id is required for Individual Animal Passport.",
        )

    factory = getattr(container, "repository_factory", None)
    if factory is None:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "REPORTING_AUTHORITY_UNAVAILABLE",
                "authority": "Lifetime Animal Passport",
                "message": "Authoritative repository factory is unavailable for Individual Animal Passport.",
            },
        )

    selected_date = (
        payload.as_of_date
        if payload.period_mode == "AS_OF_DATE"
        else operational_today
    )
    passport = DatabaseAwareLifetimeAnimalPassportService(factory).build(
        animal_id,
        as_of_date=selected_date,
    )
    if passport is None:
        raise HTTPException(status_code=404, detail=f"Animal not found: {animal_id}")

    identity = dict(passport.get("animal") or {})
    biological = dict(passport.get("biological_summary") or {})
    date_context = dict(passport.get("date_context") or {})
    schedule = dict(passport.get("schedule") or {})
    lineage = dict(passport.get("lineage") or {})
    record_counts = dict(passport.get("record_counts") or {})
    timeline = list(passport.get("timeline") or [])

    summary_row: dict[str, Any] = {
        "row_type": "SUMMARY",
        "animal_id": identity.get("animal_id", animal_id),
        "as_of_date": selected_date.isoformat(),
        "animal_type": identity.get("animal_type"),
        "lifecycle_status": identity.get("lifecycle_status"),
        "status": identity.get("status"),
        "sex": identity.get("sex"),
        "breed": identity.get("breed"),
        "date_of_birth": identity.get("date_of_birth"),
        "dam_id": identity.get("dam_id"),
        "sire_id": identity.get("sire_id"),
        "is_currently_milking": identity.get("is_currently_milking"),
        "milking_frequency": identity.get("milking_frequency"),
        "production_group": identity.get("production_group"),
        "lifetime_milk_liters": biological.get("lifetime_milk_liters"),
        "lactation_count": biological.get("lactation_count"),
        "lifetime_calvings": biological.get("lifetime_calvings"),
        "current_reproductive_status": biological.get("current_reproductive_status"),
        "current_pregnancy_status": biological.get("current_pregnancy_status"),
        "days_in_milk": biological.get("days_in_milk"),
        "open_health_cases": biological.get("open_health_cases"),
        "active_milk_withdrawal": biological.get("active_milk_withdrawal"),
        "known_ancestors": len(list(lineage.get("ancestors") or [])),
        "known_descendants": len(list(lineage.get("descendants") or [])),
        "lifetime_timeline_events": len(timeline),
        "passport_date_mode": date_context.get("mode"),
        "passport_operational_date": date_context.get("operational_date"),
    }

    for key, value in schedule.items():
        if value is None or isinstance(
            value, (str, int, float, bool, Decimal, Enum, date, datetime)
        ):
            summary_row[f"schedule_{key}"] = _scalar(value)

    rows: list[dict[str, Any]] = [summary_row]
    for event in timeline:
        if not isinstance(event, dict):
            continue
        rows.append(
            {
                "row_type": "TIMELINE",
                "animal_id": identity.get("animal_id", animal_id),
                "as_of_date": selected_date.isoformat(),
                "event_domain": _scalar(event.get("domain")),
                "event_timestamp": _scalar(event.get("timestamp")),
                "event_record": _timeline_record(event.get("record")),
            }
        )

    columns: list[str] = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)

    return {
        "dataset_status": "AUTHORITATIVE_PASSPORT_DATASET",
        "authority_status": "AUTHORITY_AVAILABLE",
        "columns": columns,
        "rows": rows,
        "summary": {
            "animal_id": identity.get("animal_id", animal_id),
            "as_of_date": selected_date.isoformat(),
            "passport_date_mode": date_context.get("mode"),
            "lifetime_milk_liters": biological.get("lifetime_milk_liters"),
            "lactation_count": biological.get("lactation_count"),
            "lifetime_calvings": biological.get("lifetime_calvings"),
            "open_health_cases": biological.get("open_health_cases"),
            "active_milk_withdrawal": biological.get("active_milk_withdrawal"),
            "timeline_events": len(timeline),
            "record_counts": "; ".join(
                f"{key}={record_counts[key]}" for key in sorted(record_counts)
            ),
        },
        "warnings": [],
    }
