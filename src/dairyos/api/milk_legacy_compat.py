"""Backward-compatible alias for the established milk summary route."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query

from dairyos.api.dependencies import get_container
from dairyos.api.milk_production_summary import milk_production_summary

router = APIRouter(prefix="/farm/milk", tags=["Milk Production"])


@router.get(
    "/production/summary",
    include_in_schema=False,
    deprecated=True,
)
def legacy_milk_production_summary(
    period: str = Query(default="7d"),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    container=Depends(get_container),
):
    return milk_production_summary(
        period=period,
        start_date=start_date,
        end_date=end_date,
        container=container,
    )
