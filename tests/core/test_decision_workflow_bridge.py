from dairyos.intelligence.workflow.integration.decision_workflow_bridge import (
    DecisionWorkflowBridge,
)

from dairyos.intelligence.workflow.gateway.workflow_gateway import (
    WorkflowGateway,
)

from dairyos.intelligence.workflow.services.workflow_orchestrator import (
    WorkflowOrchestrator,
)

from dairyos.intelligence.decision.gateway.decision_gateway import (
    DecisionGateway,
)


class DummyDecisionService:

    def decide(
        self,
        predictions,
    ):
        return []

    def get_decisions(
        self,
    ):
        return []


def test_bridge_returns_workflow_orchestrator():

    decision_gateway = DecisionGateway(
        DummyDecisionService(),
    )

    orchestrator = WorkflowOrchestrator()

    workflow_gateway = WorkflowGateway(
        orchestrator,
    )

    bridge = DecisionWorkflowBridge(
        decision_gateway,
        workflow_gateway,
    )

    assert bridge.workflow_orchestrator() is orchestrator
