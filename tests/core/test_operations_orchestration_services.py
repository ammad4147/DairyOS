from dairyos.intelligence.operations.orchestration.services.action_orchestrator import (
    ActionOrchestrator,
)

from dairyos.intelligence.operations.orchestration.services.assignment_service import (
    AssignmentService,
)

from dairyos.intelligence.operations.orchestration.services.execution_tracker import (
    ExecutionTracker,
)

from dairyos.intelligence.operations.orchestration.services.outcome_processor import (
    OutcomeProcessor,
)


def test_action_orchestrator_creates_action():

    service = ActionOrchestrator()

    action = service.create_action(
        action_type="feeding_adjustment",
        description="Increase ration for low intake animals",
        priority="high",
        source_decision="herd_intelligence",
    )

    assert action.action_type == "feeding_adjustment"
    assert action.status == "created"
    assert action.source_decision == "herd_intelligence"



def test_assignment_service_assigns_action():

    service = AssignmentService()

    assignment = service.assign(
        action_type="feeding_adjustment",
        assigned_to="farm_manager",
        assigned_role="operations",
    )

    assert assignment.action_type == "feeding_adjustment"
    assert assignment.assigned_to == "farm_manager"
    assert assignment.status == "assigned"



def test_execution_tracker_records_execution():

    service = ExecutionTracker()

    record = service.record_execution(
        action_type="feeding_adjustment",
        performed_by="farm_manager",
        notes="Completed morning adjustment",
    )

    assert record.action_type == "feeding_adjustment"
    assert record.execution_status == "completed"



def test_outcome_processor_creates_feedback():

    service = OutcomeProcessor()

    outcome = service.process(
        action_type="feeding_adjustment",
        result="Feed intake improved",
        success=True,
        feedback="Positive response",
    )

    assert outcome.action_type == "feeding_adjustment"
    assert outcome.success is True
    assert outcome.feedback == "Positive response"
