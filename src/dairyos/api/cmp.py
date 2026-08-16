from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.finance.profitability.services.cmp_scenario_service import (
    CMPScenarioService,
)

router = APIRouter(
    prefix="/farm/cmp",
    tags=["Cost of Milk Production"],
)


class CMPScenarioRequest(BaseModel):
    name: str = Field(min_length=1)
    created_by: str = Field(min_length=1)
    period_start: date
    period_end: date
    selected_cost_domains: list[str] = Field(min_length=1)
    assumptions: dict = Field(default_factory=dict)


def _serialize(row):
    return {
        "id": row.id,
        "scenario_id": row.scenario_id,
        "name": row.name,
        "created_at": (
            row.created_at.isoformat()
            if row.created_at
            else None
        ),
        "created_by": row.created_by,
        "period_start": row.period_start.isoformat(),
        "period_end": row.period_end.isoformat(),
        "currency": row.currency,
        "basis": row.basis,
        "selected_cost_domains": row.selected_cost_domains,
        "assumptions": row.assumptions,
        "milk_volume_litres": row.milk_volume_litres,
        "eligible_cost": row.eligible_cost,
        "cmp_per_litre": row.cmp_per_litre,
        "status": row.status,
    }


@router.post("/scenarios")
def create_cmp_scenario(payload: CMPScenarioRequest):
    factory = RepositoryFactory.create()

    try:
        service = CMPScenarioService(factory)

        try:
            row, evaluation = service.create(
                name=payload.name,
                created_by=payload.created_by,
                period_start=payload.period_start,
                period_end=payload.period_end,
                selected_cost_domains=payload.selected_cost_domains,
                assumptions=payload.assumptions,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail=str(exc),
            ) from exc

        return {
            "scenario": _serialize(row),
            "evaluation": evaluation,
        }
    finally:
        factory.close()


@router.get("/scenarios")
def list_cmp_scenarios():
    factory = RepositoryFactory.create()

    try:
        service = CMPScenarioService(factory)

        return {
            "scenarios": [
                _serialize(row)
                for row in service.list()
            ]
        }
    finally:
        factory.close()


@router.get("/scenarios/{scenario_id}")
def get_cmp_scenario(scenario_id: str):
    factory = RepositoryFactory.create()

    try:
        row = CMPScenarioService(factory).get(scenario_id)

        if row is None:
            raise HTTPException(
                status_code=404,
                detail="CMP scenario not found",
            )

        return {
            "scenario": _serialize(row),
        }
    finally:
        factory.close()
