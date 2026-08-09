from dairyos.intelligence.workflow.services.workflow_service import (
    WorkflowService,
)

from dairyos.intelligence.workflow.services.workflow_execution_service import (
    WorkflowExecutionService,
)

from dairyos.intelligence.workflow.services.workflow_state_service import (
    WorkflowStateService,
)

from dairyos.intelligence.workflow.services.workflow_history_service import (
    WorkflowHistoryService,
)


class WorkflowOrchestrator:
    """
    Enterprise workflow orchestration service.

    Coordinates the complete workflow lifecycle.

    Responsibilities:

    - create workflow
    - execute workflow
    - manage workflow state
    - record workflow outcome

    Future extensions:

    - autonomous orchestration
    - event-driven execution
    - decision integration
    - distributed workflows
    """

    def __init__(self):

        self.workflow_service = WorkflowService()

        self.execution_service = (
            WorkflowExecutionService()
        )

        self.state_service = (
            WorkflowStateService()
        )

        self.history_service = (
            WorkflowHistoryService()
        )
