from dairyos.app import container

from dairyos.operations.command_center.operations_command_center_orchestrator import (
    OperationsCommandCenterOrchestrator,
)


def test_command_center_default_green_state():

    orchestrator = (
        OperationsCommandCenterOrchestrator(
            container.runtime
        )
    )

    result = (
        orchestrator.generate_command_center()
    )

    assert result["operational_status"] == "GREEN"
    assert result["priority_level"] == "NORMAL"
    assert (
        result["management_attention_required"]
        is False
    )
    assert result["risk_level"] == "LOW"
    assert result["action_required"] is False


def test_command_center_output_contains_management_focus():

    orchestrator = (
        OperationsCommandCenterOrchestrator(
            container.runtime
        )
    )

    result = (
        orchestrator.generate_command_center()
    )

    assert (
        result["recommended_focus"]
        == "Maintain operational performance"
    )


def test_command_center_performance_score_flow():

    orchestrator = (
        OperationsCommandCenterOrchestrator(
            container.runtime
        )
    )

    result = (
        orchestrator.generate_command_center()
    )

    assert result["performance_score"] == 100.0


def test_command_center_structure():

    orchestrator = (
        OperationsCommandCenterOrchestrator(
            container.runtime
        )
    )

    result = (
        orchestrator.generate_command_center()
    )

    required_fields = [
        "operational_status",
        "priority_level",
        "active_actions",
        "performance_score",
        "management_attention_required",
        "recommended_focus",
        "executive_status",
        "risk_level",
        "action_required",
    ]

    for field in required_fields:
        assert field in result
