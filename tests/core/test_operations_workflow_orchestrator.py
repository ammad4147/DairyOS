from datetime import datetime

from dairyos.operations.workflow.models.operational_workflow_event import (
    OperationalWorkflowEvent,
)

from dairyos.operations.workflow.services.operations_workflow_orchestrator import (
    OperationsWorkflowOrchestrator,
)


def test_workflow_creates_operational_chain():

    service = OperationsWorkflowOrchestrator()

    event = OperationalWorkflowEvent(
        event_id="WF-001",
        source="operations_intelligence",
        category="Feeding",
        priority="HIGH",
        description="Feed delay detected",
        created_at=datetime.now(),
    )

    service.submit_event(event)

    result = service.process_event(event)

    assert result.decision_created is True
    assert result.action_created is True
    assert result.outcome_tracking_enabled is True
    assert result.workflow_status == "ACTIVE"
