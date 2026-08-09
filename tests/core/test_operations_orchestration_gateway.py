from dairyos.intelligence.operations.orchestration.gateway.operations_orchestration_gateway import (
    OperationsOrchestrationGateway,
)


def test_gateway_create_action():
    gateway = OperationsOrchestrationGateway()

    action = gateway.create_action(
        action_type="feeding",
        description="Increase feed allocation",
        priority="high",
        source_decision="nutrition_engine",
    )

    assert action.action_type == "feeding"
    assert action.description == "Increase feed allocation"
    assert action.priority == "high"
    assert action.status == "pending"
    assert action.source_decision == "nutrition_engine"


def test_gateway_assign_action():
    gateway = OperationsOrchestrationGateway()

    assignment = gateway.assign_action(
        action_type="feeding",
        assigned_to="farm_manager",
        assigned_role="manager",
    )

    assert assignment.action_type == "feeding"
    assert assignment.assigned_to == "farm_manager"
    assert assignment.assigned_role == "manager"
    assert assignment.status == "assigned"


def test_gateway_record_execution():
    gateway = OperationsOrchestrationGateway()

    execution = gateway.record_execution(
        action_type="feeding",
        performed_by="farm_manager",
        notes="Completed successfully",
    )

    assert execution.action_type == "feeding"
    assert execution.performed_by == "farm_manager"
    assert execution.execution_status == "completed"
    assert execution.notes == "Completed successfully"


def test_gateway_record_outcome():
    gateway = OperationsOrchestrationGateway()

    outcome = gateway.record_outcome(
        action_type="feeding",
        result="Milk production improved",
        feedback="Positive outcome",
        success=True,
    )

    assert outcome.action_type == "feeding"
    assert outcome.result == "Milk production improved"
    assert outcome.feedback == "Positive outcome"
    assert outcome.success is True
