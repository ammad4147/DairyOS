from fastapi import APIRouter

from dairyos.operations.health.services.operations_health_service import (
    OperationsHealthService,
)


router = APIRouter(
    prefix="/operations",
    tags=["Operations"],
)


@router.get("/health")
def operations_health():

    snapshot = OperationsHealthService().generate_snapshot()

    return {
        "health_status": snapshot.health_status,
        "operational_score": snapshot.operational_score,
        "active_decisions": snapshot.active_decisions,
        "pending_actions": snapshot.pending_actions,
        "tracked_outcomes": snapshot.tracked_outcomes,
        "learning_signals": snapshot.learning_signals,
        "owner_attention_required": snapshot.owner_attention_required,
    }
