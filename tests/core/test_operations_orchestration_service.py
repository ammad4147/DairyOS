from dairyos.intelligence.operations.orchestration.models.operational_action import (
    OperationalAction,
)

from dairyos.intelligence.operations.orchestration.services.orchestration_service import (
    OrchestrationService,
)

from dairyos.intelligence.operations.orchestration.services.operations_orchestration_service import (
    OperationsOrchestrationService,
)


def test_create_action():
    service = OrchestrationService()

    action = service.create_action(
        action_type="feeding_adjustment",
        description="Increase feed allocation for low intake cows",
        priority="high",
        source_decision="herd_intelligence_engine",
    )

    assert action.action_type == "feeding_adjustment"
    assert action.status == "pending"


def test_assign_action():
    service = OrchestrationService()

    assignment = service.assign_action(
        action_type="feeding_adjustment",
        assigned_to="farm_manager",
        assigned_role="operations",
    )

    assert assignment.action_type == "feeding_adjustment"
    assert assignment.assigned_to == "farm_manager"
    assert assignment.assigned_role == "operations"
    assert assignment.status == "assigned"


def test_record_execution_uses_canonical_operational_execution():
    service = OrchestrationService()

    record = service.record_execution(
        action_type="health_check",
        performed_by="farm_manager",
        notes="Inspection completed",
    )

    assert record.action_type == "health_check"
    assert record.performed_by == "farm_manager"
    assert record.execution_status == "completed"

    canonical = record.canonical_execution

    assert canonical is not None
    assert canonical.action_id == "health_check"
    assert canonical.assigned_to == "farm_manager"
    assert canonical.status == canonical.COMPLETED
    assert canonical.completed_by == "farm_manager"
    assert canonical.completed_at is not None


def test_operations_orchestration_record_execution_uses_canonical_execution():
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

    canonical = record.canonical_execution

    assert canonical is not None
    assert canonical.action_id == "health_check"
    assert canonical.assigned_to == "farm_manager"
    assert canonical.status == canonical.COMPLETED
    assert canonical.completed_by == "farm_manager"
    assert canonical.completed_at is not None


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
