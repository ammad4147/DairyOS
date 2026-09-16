"""Authoritative Reporting projections for governed DairyOS TMR data."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from fastapi import HTTPException

from dairyos.api.tmr import build_live_tmr_summary, tmr_feed_cost_for_period


def _factory(container: Any) -> Any:
    factory = getattr(container, "repository_factory", None)
    if factory is None:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "REPORTING_AUTHORITY_UNAVAILABLE",
                "authority": "TMR",
                "message": "Governed TMR repository authority is unavailable.",
            },
        )
    return factory


def _category_filter(payload: Any) -> str | None:
    value = payload.filters.get("category")
    if value is None or str(value).strip().upper() == "ALL":
        return None
    wanted = str(value).strip().upper()
    aliases = {
        "MILKING": "Milking",
        "MILKING COW": "Milking",
        "MILKING COWS": "Milking",
        "DRY": "Dry",
        "DRY COW": "Dry",
        "DRY COWS": "Dry",
        "HEIFER": "Heifer",
        "HEIFERS": "Heifer",
        "FEMALE CALF": "Female Calf",
        "FEMALE CALVES": "Female Calf",
        "MALE CALF": "Male Calf",
        "MALE CALVES": "Male Calf",
        "BULL": "Bull",
        "BULLS": "Bull",
    }
    selected = aliases.get(wanted)
    if selected is None:
        raise HTTPException(status_code=422, detail="Unsupported TMR Reporting category filter.")
    return selected


def _ingredient_filter(payload: Any) -> str | None:
    value = payload.filters.get("ingredient")
    if value is None or str(value).strip().upper() == "ALL":
        return None
    return str(value).strip()


def _current_rows(summary: dict[str, Any], payload: Any) -> list[dict[str, Any]]:
    category_filter = _category_filter(payload)
    ingredient_filter = _ingredient_filter(payload)
    categories = {
        str(row.get("category")): row
        for row in summary.get("categories", [])
        if isinstance(row, dict)
    }
    rows: list[dict[str, Any]] = []
    for stage_key, stage in (summary.get("stages") or {}).items():
        if not isinstance(stage, dict):
            continue
        stage_categories = [
            name
            for name, category in categories.items()
            if stage_key in list(category.get("stage_keys") or [])
        ]
        if category_filter is not None and category_filter not in stage_categories:
            continue
        for ingredient in stage.get("ingredients", []) or []:
            if not isinstance(ingredient, dict):
                continue
            name = str(ingredient.get("catalog_name") or "")
            if ingredient_filter is not None and name.casefold() != ingredient_filter.casefold():
                continue
            rows.append(
                {
                    "operational_date": summary.get("operational_date"),
                    "stage": stage_key,
                    "stage_label": stage.get("label"),
                    "categories": ", ".join(stage_categories),
                    "ingredient": name,
                    "quantity": ingredient.get("quantity"),
                    "dose_unit": ingredient.get("dose_unit"),
                    "price_per_kg": ingredient.get("price_per_kg"),
                    "price_source": ingredient.get("price_source"),
                    "selected_price_source": ingredient.get("selected_price_source"),
                    "finance_transaction_id": ingredient.get("finance_transaction_id"),
                    "finance_purchase_date": ingredient.get("finance_purchase_date"),
                    "cost_per_head_day": ingredient.get("cost_per_head_day"),
                }
            )
    return rows


def _historical_period(payload: Any, operational_today: date) -> tuple[date, date]:
    if payload.period_mode == "AS_OF_DATE":
        selected = payload.as_of_date
        if selected is None:
            raise HTTPException(status_code=422, detail="as_of_date is required for Historical TMR.")
        return selected, selected
    if payload.period_mode == "DATE_RANGE":
        if payload.start_date is None or payload.end_date is None:
            raise HTTPException(status_code=422, detail="start_date and end_date are required for Historical TMR.")
        return payload.start_date, payload.end_date
    raise HTTPException(status_code=422, detail="Unsupported Historical TMR period mode.")


def _historical_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "operational_date": row.get("date"),
            "feed_cost": row.get("feed_cost"),
            "basis": row.get("basis"),
            "record_id": row.get("record_id"),
            "locked_at": row.get("locked_at"),
        }
        for row in result.get("daily", [])
    ]


def tmr_reporting_dataset(payload: Any, container: Any, operational_today: date) -> dict[str, Any]:
    """Project current or historical TMR without creating a second authority."""
    factory = _factory(container)

    if payload.report_id == "current-tmr":
        selected = payload.operational_date if payload.period_mode == "OPERATIONAL_DATE" else operational_today
        if selected != operational_today:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "CURRENT_TMR_REQUIRES_CURRENT_OPERATIONAL_DATE",
                    "message": "Current TMR cannot reconstruct a historical herd or ration. Use Historical TMR for prior operational dates.",
                },
            )
        summary = build_live_tmr_summary(factory, operational_date=selected)
        rows = _current_rows(summary, payload)
        return {
            "dataset_status": "AUTHORITATIVE_CURRENT_TMR_DATASET",
            "authority_status": "AUTHORITY_AVAILABLE",
            "columns": list(rows[0].keys()) if rows else [],
            "rows": rows,
            "summary": {
                "operational_date": summary.get("operational_date"),
                "herd_counts": summary.get("herd_counts", {}),
                "total_herd_feed_cost_per_day": summary.get("total_herd_feed_cost_per_day"),
                "milk_production_today_liters": summary.get("milk_production_today_liters"),
                "feed_cost_per_litre_today": summary.get("feed_cost_per_litre_today"),
                "feed_cost_basis": summary.get("feed_cost_basis"),
            },
            "warnings": [] if rows else ["No current governed TMR rows match the selected filters."],
        }

    if payload.report_id != "historical-tmr":
        raise HTTPException(status_code=422, detail="Unsupported TMR Reporting report.")

    start, end = _historical_period(payload, operational_today)
    result = tmr_feed_cost_for_period(factory, start, end)
    missing = list(result.get("missing_authority_days") or [])
    if missing:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "HISTORICAL_TMR_AUTHORITY_MISSING",
                "authority": "TMR_DAILY_12_00_SNAPSHOT",
                "missing_authority_days": missing,
                "message": "Historical TMR cannot be reconstructed from the current ration or current herd state.",
            },
        )

    rows = _historical_rows(result)
    return {
        "dataset_status": "AUTHORITATIVE_HISTORICAL_TMR_DATASET",
        "authority_status": "AUTHORITY_AVAILABLE",
        "columns": list(rows[0].keys()) if rows else ["operational_date", "feed_cost", "basis", "record_id", "locked_at"],
        "rows": rows,
        "summary": {
            "total_feed_cost": result.get("total_feed_cost"),
            "locked_days": result.get("locked_days", 0),
            "provisional_days": result.get("provisional_days", 0),
            "complete": result.get("complete", False),
            "source": result.get("source"),
            "requested_period": result.get("requested_period"),
            "effective_period": result.get("effective_period"),
            "clamped_to_operational_date": result.get("clamped_to_operational_date", False),
        },
        "warnings": [],
    }
