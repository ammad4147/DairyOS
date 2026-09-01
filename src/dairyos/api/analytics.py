"""Governed Data Analytics and implementation-contract backend boundary."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from dairyos.farm.operations.services.analytics_contract_service import (
    AnalyticsContractService,
)
from dairyos.farm.operations.services.reconciled_implementation_contract_service import (
    ReconciledImplementationContractService,
)


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

@router.get("/integrated")
def get_integrated_analytics():
    """
    Returns: kpis with severity + actionTab, and chart-ready data arrays.
    """
    # TODO: Implement integrated analytics aggregation
    return {
        "kpis": [],
        "charts": {},
        "message": "Integrated Analytics - placeholder"
    }
