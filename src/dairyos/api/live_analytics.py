from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from dairyos.farm.operations.services.live_analytics_service import LiveAnalyticsService


router = APIRouter(prefix="/farm/analytics-live", tags=["Live Analytics"])


@router.get("")
def live_analytics(days: int = Query(default=30, ge=1, le=365)):
    try:
        return LiveAnalyticsService().build(days=days)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
