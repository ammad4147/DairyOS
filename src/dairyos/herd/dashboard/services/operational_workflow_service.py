from ..models.operational_workflow import OperationalWorkflow



class OperationalWorkflowService:



    def create_workflow(

        self,

        name,

        steps

    ):


        return OperationalWorkflow(

            name,

            steps,

            "PENDING"

        )



    def complete_step(

        self,

        workflow,

        step

    ):


        if step in workflow.steps:

            workflow.steps.remove(step)


        if len(workflow.steps) == 0:

            workflow.status = "COMPLETED"


        return workflow



    def is_complete(

        self,

        workflow

    ):


        return workflow.status == "COMPLETED"
