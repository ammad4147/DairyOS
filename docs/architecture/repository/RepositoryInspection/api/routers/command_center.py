from fastapi import APIRouter

from dairyos.operations.command_center.operations_command_center_orchestrator import (
    OperationsCommandCenterOrchestrator,
)


router = APIRouter(
    tags=["Command Center"],
)


@router.get("/command-center")
def command_center():

    orchestrator = (
        OperationsCommandCenterOrchestrator()
    )

    command_view = (
        orchestrator.generate_command_center()
    )

    return {
        "system": "DairyOS",
        "module": "Command Center",
        "status": "AVAILABLE",
        "orchestrator": "ACTIVE",
        "operational_status": (
            command_view["operational_status"]
        ),
        "priority_level": (
            command_view["priority_level"]
        ),
        "active_actions": (
            command_view["active_actions"]
        ),
        "performance_score": (
            command_view["performance_score"]
        ),
        "management_attention_required": (
            command_view[
                "management_attention_required"
            ]
        ),
        "recommended_focus": (
            command_view["recommended_focus"]
        ),
        "executive_status": (
            command_view["executive_status"]
        ),
        "risk_level": (
            command_view["risk_level"]
        ),
        "action_required": (
            command_view["action_required"]
        ),
    }
