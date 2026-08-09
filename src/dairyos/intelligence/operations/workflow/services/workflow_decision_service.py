from dairyos.intelligence.operations.workflow.models.workflow_decision import (
    WorkflowDecision,
)



class WorkflowDecisionService:
    """
    Generates operational decisions from
    workflow alerts using deterministic rules.

    No AI inference is performed.
    """


    def __init__(
        self,
        alert_service,
    ):

        self.alert_service = alert_service



    def generate_decisions(
        self,
    ):

        decisions = []


        for workflow in self.alert_service.stalled_workflows():

            decisions.append(

                WorkflowDecision(

                    workflow_id=workflow.workflow_id,

                    decision_type="stalled_workflow",

                    severity="high",

                    recommended_action=(

                        "Escalate workflow to responsible supervisor"

                    ),

                )

            )



        for workflow in self.alert_service.overdue_workflows():

            decisions.append(

                WorkflowDecision(

                    workflow_id=workflow.workflow_id,

                    decision_type="overdue_workflow",

                    severity="critical",

                    recommended_action=(

                        "Immediate operational review required"

                    ),

                )

            )



        workload = (
            self.alert_service.workload_imbalance()
        )


        for operator, count in workload.items():

            if count >= 3:

                decisions.append(

                    WorkflowDecision(

                        workflow_id="system",

                        decision_type="workload_imbalance",

                        severity="medium",

                        recommended_action=(

                            f"Review workload allocation for {operator}"

                        ),

                    )

                )



        return decisions
