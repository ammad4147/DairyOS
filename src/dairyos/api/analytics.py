"""Governed Data Analytics backend contract."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from dairyos.farm.operations.services.analytics_contract_service import (
    AnalyticsContractService,
)


router = APIRouter(
    prefix="/farm/analytics",
    tags=["Data Analytics"],
)


@router.get("/catalog")
def analytics_catalog():
    """Return the authoritative analytics contract catalog."""
    return AnalyticsContractService.catalog()


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
