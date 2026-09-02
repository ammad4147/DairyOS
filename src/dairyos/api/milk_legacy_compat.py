"""Backward-compatible aliases for established milk routes."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query

from dairyos.api.dependencies import get_container
from dairyos.api.milk_production_summary import milk_production_summary
from dairyos.farm.production.services.milk_inventory_capacity_service import (
    overall_saleable_capacity,
)

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


@router.get("/capacity")
def milk_capacity(
    through_date: date = Query(...),
    container=Depends(get_container),
):
    """Return the governed carried saleable-milk balance through a date.

    MilkTab historically consumes this route for its overall reconciliation
    card. The underlying capacity service remained authoritative after the
    HTTP route was retired, so this compatibility boundary restores the
    established contract without duplicating any milk arithmetic in the UI.
    """

    factory = getattr(container, "repository_factory", None)
    return overall_saleable_capacity(
        through_date,
        factory=factory,
    )
