from dairyos.intelligence.workflow.gateway.workflow_gateway import (
    WorkflowGateway,
)

from dairyos.intelligence.workflow.services.workflow_orchestrator import (
    WorkflowOrchestrator,
)


def test_gateway_returns_orchestrator():

    orchestrator = WorkflowOrchestrator()

    gateway = WorkflowGateway(
        orchestrator,
    )

    assert gateway.orchestrator_service() is orchestrator
