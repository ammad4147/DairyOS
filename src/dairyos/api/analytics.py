"""Governed Data Analytics and implementation-contract backend boundary."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from dairyos.farm.operations.services.analytics_contract_service import (
    AnalyticsContractService,
)
from dairyos.farm.operations.services.reconciled_implementation_contract_service import (
    ReconciledImplementationContractService,
)
from dairyos.farm.operations.services.live_analytics_service import LiveAnalyticsService
from dairyos.api.dependencies import get_container


router = APIRouter(
    prefix="/farm/analytics",
    tags=["Data Analytics"],
)


@router.get("/catalog")
def analytics_catalog():
    """Return the authoritative analytics contract catalog."""
    return AnalyticsContractService.catalog()


@router.get("/implementation-contract")
def implementation_contract():
    """Return the reconciled backend capability/dependency registry."""
    return ReconciledImplementationContractService.catalog()


@router.get("/implementation-contract/{capability}")
def implementation_capability(capability: str):
    """Return one reconciled capability contract."""
    try:
        return ReconciledImplementationContractService.capability(
            capability
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown implementation capability: {capability}",
        ) from exc


@router.get("/integrated")
def get_integrated_analytics(
    days: int = Query(default=30, ge=1, le=365),
    container=Depends(get_container),
):
    """Return the integrated analytics read model from governed authorities."""
    try:
        live = LiveAnalyticsService().build(
            days=days,
            repository_factory=container.repository_factory,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    financial = live.get("financial", {})
    health = live.get("health_summary", {})
    breeding = live.get("breeding_cycle_analytics", {})
    return {
        **live,
        "kpis": {
            "milk_litres": financial.get("milk_litres"),
            "feed_cost_per_litre": financial.get("feed_cost_per_litre"),
            "opex_cost_per_litre": financial.get("opex_cost_per_litre"),
            "cost_of_milk_production_per_litre": financial.get(
                "cost_of_milk_production_per_litre"
            ),
            "active_herd": live.get("herd_dynamics", {}).get("active_herd", 0),
            "open_health_cases": health.get("open_cases", 0),
            "conception_rate_percent": breeding.get(
                "herd_conception_rate_percent"
            ),
        },
        "charts": {
            "milk_environment": live.get("milk_environment", []),
            "health": live.get("health", []),
            "health_summary": health,
            "breeding": live.get("breeding", []),
            "breeding_cycle_analytics": breeding,
            "herd_dynamics": live.get("herd_dynamics", {}),
        },
    }


@router.get("/{analysis}")
def analytics_contract(analysis: str):
    """Return the authoritative contract for one analysis."""
    try:
        return AnalyticsContractService.get_analysis(analysis)
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown analytics analysis: {analysis}",
        ) from exc
