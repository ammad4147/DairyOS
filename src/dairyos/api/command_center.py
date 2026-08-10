from fastapi import APIRouter, HTTPException

from dairyos.api.dependencies import get_container
from dairyos.domain.commands import Command


router = APIRouter(tags=["Command Center"])


@router.get("/command-center")
def command_center():
    container = get_container()
    operational_command_center = container.operational_command_center_service.snapshot()
    return container.command_center_projection_service.build_view(
        operational_command_center=operational_command_center
    )


@router.post("/command-center/decisions/{decision_id}/acknowledge")
def acknowledge_decision(decision_id: str, payload: dict):
    container = get_container()
    operator = str(payload.get("operator") or "UI Operator").strip()
    if not operator:
        raise HTTPException(status_code=400, detail="operator is required")
    try:
        return container.operational_command_center_service.acknowledge_decision(
            decision_id=decision_id,
            operator=operator,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/command-center/decisions/{decision_id}/resolve")
def resolve_decision(decision_id: str, payload: dict):
    container = get_container()
    operator = str(payload.get("operator") or "UI Operator").strip()
    outcome = payload.get("outcome")
    if not operator:
        raise HTTPException(status_code=400, detail="operator is required")
    try:
        return container.operational_command_center_service.resolve_decision(
            decision_id=decision_id,
            operator=operator,
            outcome=outcome,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/command-center/actions/{action_id}/status")
def update_action(action_id: str, payload: dict):
    container = get_container()
    status = str(payload.get("status") or "").strip().upper()
    operator = payload.get("operator")
    if status not in {"IN_PROGRESS", "COMPLETED", "VERIFIED", "CLOSED"}:
        raise HTTPException(status_code=400, detail="invalid action status")
    try:
        return container.operational_command_center_service.update_action(
            action_id=action_id,
            status=status,
            operator=operator,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/animals")
def create_animal(payload: dict):
    container = get_container()
    container.operations.handle_command(Command(name="CreateAnimal", payload=payload))
    return {"status": "ok"}


@router.post("/milk")
def record_milk(payload: dict):
    container = get_container()
    container.operations.handle_command(Command(name="RecordMilk", payload=payload))
    return {"status": "ok"}


@router.post("/feed")
def feed_animal(payload: dict):
    container = get_container()
    container.operations.handle_command(Command(name="FeedAnimal", payload=payload))
    return {"status": "ok"}
