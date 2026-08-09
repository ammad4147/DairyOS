from dairyos.operations.workflows.models.operational_workflow import (
    OperationalWorkflow,
)



class WorkflowService:
    """
    Creates and manages operational workflows.
    """



    def __init__(
        self,
    ):

        self.workflows = []



    def create(
        self,
        workflow: OperationalWorkflow,
    ):

        self.workflows.append(
            workflow
        )

        return workflow



    def all(
        self,
    ):

        return list(
            self.workflows
        )



    def count(
        self,
    ):

        return len(
            self.workflows
        )

