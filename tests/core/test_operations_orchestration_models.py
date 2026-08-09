from dairyos.intelligence.operations.orchestration.models.operational_action import (
    OperationalAction,
)

from dairyos.intelligence.operations.orchestration.models.action_assignment import (
    ActionAssignment,
)

from dairyos.intelligence.operations.orchestration.models.execution_record import (
    ExecutionRecord,
)

from dairyos.intelligence.operations.orchestration.models.action_outcome import (
    ActionOutcome,
)


def test_operational_action_creation():

    action = OperationalAction(
        action_type="feeding_adjustment",
        description="Increase feed allocation for low intake cows",
        priority="high",
        status="generated",
        source_decision="herd_intelligence_engine",
    )

    assert action.action_type == "feeding_adjustment"
    assert action.description == "Increase feed allocation for low intake cows"
    assert action.priority == "high"
    assert action.status == "generated"
    assert action.source_decision == "herd_intelligence_engine"



def test_action_assignment_creation():

    assignment = ActionAssignment(
        action_type="feeding_adjustment",
        assigned_to="farm_manager",
        assigned_role="operations",
        status="assigned",
    )

    assert assignment.action_type == "feeding_adjustment"
    assert assignment.assigned_to == "farm_manager"
    assert assignment.assigned_role == "operations"
    assert assignment.status == "assigned"



def test_execution_record_creation():

    record = ExecutionRecord(
        action_type="feeding_adjustment",
        performed_by="farm_manager",
        execution_status="completed",
        notes="Feed allocation updated successfully",
    )

    assert record.action_type == "feeding_adjustment"
    assert record.performed_by == "farm_manager"
    assert record.execution_status == "completed"
    assert record.notes == "Feed allocation updated successfully"



def test_action_outcome_creation():

    outcome = ActionOutcome(
        action_type="feeding_adjustment",
        result="Feed adjustment completed successfully",
        success=True,
        feedback="Positive intake response observed",
    )

    assert outcome.action_type == "feeding_adjustment"
    assert outcome.result == "Feed adjustment completed successfully"
    assert outcome.success is True
    assert outcome.feedback == "Positive intake response observed"
