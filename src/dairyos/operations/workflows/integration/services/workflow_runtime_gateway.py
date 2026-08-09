from dairyos.operations.workflows.services.workflow_service import (
    WorkflowService,
)



class WorkflowRuntimeGateway:
    """
    Runtime boundary for operational workflows.

    Keeps workflow domain isolated from
    platform bootstrap concerns.
    """


    def __init__(
        self,
        workflow_service: WorkflowService,
    ):

        self.workflow_service = workflow_service



    def create(
        self,
        workflow,
    ):

        return self.workflow_service.create(
            workflow
        )



    def all(
        self,
    ):

        return self.workflow_service.all()



    def count(
        self,
    ):

        return self.workflow_service.count()

