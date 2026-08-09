from dairyos.intelligence.decision.gateway.decision_gateway import (
    DecisionGateway,
)

from dairyos.intelligence.workflow.gateway.workflow_gateway import (
    WorkflowGateway,
)


class DecisionWorkflowBridge:
    """
    Integrates decision intelligence
    with workflow intelligence.

    Responsibilities:

    - receive decision recommendations
    - initiate workflow orchestration

    Future extensions:

    - automatic workflow selection
    - approval routing
    - event-driven orchestration
    """


    def __init__(
        self,
        decision_gateway: DecisionGateway,
        workflow_gateway: WorkflowGateway,
    ):

        self.decision_gateway = decision_gateway

        self.workflow_gateway = workflow_gateway


    def workflow_orchestrator(self):

        return self.workflow_gateway.orchestrator_service()
