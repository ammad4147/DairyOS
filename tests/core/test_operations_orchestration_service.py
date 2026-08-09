from dairyos.intelligence.operations.orchestration.models.operational_action import (
    OperationalAction,
)

from dairyos.intelligence.operations.orchestration.services.operations_orchestration_service import (
    OperationsOrchestrationService,
)


def test_create_assignment():

    service = OperationsOrchestrationService()

    action = OperationalAction(
        action_type="feeding_adjustment",
        description="Increase feed allocation for low intake cows",
        priority="high",
        status="generated",
        source_decision="herd_intelligence_engine",
    )

    assignment = service.create_assignment(
        action,
        "farm_manager",
        "operations",
    )

    assert assignment.action_type == "feeding_adjustment"
    assert assignment.assigned_to == "farm_manager"
    assert assignment.assigned_role == "operations"
    assert assignment.status == "assigned"



def test_record_execution():

    service = OperationsOrchestrationService()

    action = OperationalAction(
        action_type="health_check",
        description="Inspect cows with reduced activity",
        priority="medium",
        status="generated",
        source_decision="health_intelligence_engine",
    )

    record = service.record_execution(
        action,
        "farm_manager",
        "Inspection completed",
    )

    assert record.action_type == "health_check"
    assert record.performed_by == "farm_manager"
    assert record.execution_status == "completed"



def test_create_outcome():

    service = OperationsOrchestrationService()

    action = OperationalAction(
        action_type="ration_update",
        description="Modify ration according to intake trend",
        priority="high",
        status="generated",
        source_decision="nutrition_intelligence_engine",
    )

    outcome = service.create_outcome(
        action,
        "Ration updated successfully",
        True,
        "Feed intake improved",
    )

    assert outcome.action_type == "ration_update"
    assert outcome.success is True
    assert outcome.result == "Ration updated successfully"
