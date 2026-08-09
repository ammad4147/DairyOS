from fastapi import APIRouter

from dairyos.operations.executive.services.executive_operations_service import (
    ExecutiveOperationsService,
)


router = APIRouter(
    prefix="/operations",
    tags=["Operations"],
)


@router.get("/executive")
def executive_summary():

    service = ExecutiveOperationsService()

    summary = service.generate_summary()

    return {
        "health_status": summary.health_status,
        "attention_count": summary.attention_count,
        "critical_issue_count": summary.critical_issue_count,
        "owner_action_required": summary.owner_action_required,
        "recommended_focus": summary.recommended_focus,
        "operational_priority_score": summary.operational_priority_score,
        "critical_items": summary.critical_items,
    }
