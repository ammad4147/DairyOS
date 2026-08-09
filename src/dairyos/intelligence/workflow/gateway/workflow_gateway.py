from dairyos.intelligence.workflow.services.workflow_orchestrator import (
    WorkflowOrchestrator,
)


class WorkflowGateway:
    """
    Gateway boundary for workflow orchestration.
    """

    def __init__(self, orchestrator=None):

        if orchestrator is None:
            orchestrator = WorkflowOrchestrator()

        self.orchestrator = orchestrator


    def orchestrator_service(self):

        return self.orchestrator


    def execute(self, workflow):

        return self.orchestrator.execute(
            workflow
        )
