from fastapi import APIRouter

from dairyos.operations.command.services.operations_command_service import (
    OperationsCommandService,
)


router = APIRouter(
    prefix="/operations",
    tags=["Operations"],
)


@router.get("/commands/status")
def command_status():

    status = OperationsCommandService().generate_status()


    return {
        "health_status": status.health_status,
        "active_attention_count": status.active_attention_count,
        "recommended_focus": status.recommended_focus,
        "has_critical_attention": status.has_critical_attention,
    }
