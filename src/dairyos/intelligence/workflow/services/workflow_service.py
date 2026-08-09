from dairyos.intelligence.workflow.models.workflow import (
    Workflow,
)


class WorkflowService:
    """
    Enterprise workflow service.
    """

    def create(
        self,
        workflow_type: str,
        description: str,
        initiated_by: str,
    ) -> Workflow:

        return Workflow(
            workflow_type=workflow_type,
            description=description,
            status="pending",
            initiated_by=initiated_by,
        )
