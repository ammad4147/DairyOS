from dairyos.operations.executive.models.executive_operations_summary import (
    ExecutiveOperationsSummary,
)

from dairyos.operations.executive.services.operations_command_bridge import (
    OperationsCommandBridge,
)


def test_operations_bridge_green():

    summary = ExecutiveOperationsSummary(
        health_status="GREEN",
        attention_count=0,
        critical_issue_count=0,
        owner_action_required=False,
        recommended_focus="Operations stable",
        operational_priority_score=10.0,
    )

    bridge = OperationsCommandBridge()

    result = bridge.translate(summary)

    assert result["domain"] == "OPERATIONS"
    assert result["risk_level"] == "LOW"


def test_operations_bridge_red():

    summary = ExecutiveOperationsSummary(
        health_status="RED",
        attention_count=2,
        critical_issue_count=1,
        owner_action_required=True,
        recommended_focus="Immediate action",
        operational_priority_score=90.0,
        critical_items=[
            "Feed delay"
        ],
    )

    bridge = OperationsCommandBridge()

    result = bridge.translate(summary)

    assert result["risk_level"] == "HIGH"
    assert result["owner_action_required"] is True
