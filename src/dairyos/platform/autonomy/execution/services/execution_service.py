from dairyos.platform.autonomy.execution.models.action_plan import (
    ActionPlan,
)



class ExecutionService:
    """
    Controls autonomous action workflow.
    """



    def create_plan(

        self,

        title,

        description,

        assigned_to,

        priority,

    ):


        return ActionPlan(

            title=title,

            description=description,

            assigned_to=assigned_to,

            priority=priority,

        )



    def approve(

        self,

        plan,

    ):


        plan.status = "approved"

        return plan



    def complete(

        self,

        plan,

    ):


        plan.status = "completed"

        return plan

