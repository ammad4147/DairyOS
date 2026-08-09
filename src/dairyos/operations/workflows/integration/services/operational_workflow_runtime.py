from dairyos.operations.workflows.services.workflow_service import (
    WorkflowService,
)


from dairyos.operations.workflows.integration.services.workflow_runtime_gateway import (
    WorkflowRuntimeGateway,
)


from dairyos.operations.workflows.integration.services.workflow_event_publisher import (
    WorkflowEventPublisher,
)



class OperationalWorkflowRuntime:
    """
    Runtime container for operational workflows.

    Provides a stable integration boundary
    between workflow domain services and
    enterprise runtime.
    """


    def __init__(
        self,
        event_publisher=None,
    ):

        self.workflow_service = WorkflowService()


        self.workflow_gateway = WorkflowRuntimeGateway(
            self.workflow_service
        )


        self.workflow_event_publisher = None


        if event_publisher is not None:

            self.workflow_event_publisher = WorkflowEventPublisher(
                event_publisher
            )
