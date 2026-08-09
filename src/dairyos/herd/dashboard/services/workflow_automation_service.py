from ..models.workflow_automation import WorkflowAutomation



class WorkflowAutomationService:



    def generate_workflow(

        self,

        trigger

    ):


        if "production" in trigger.lower():

            return WorkflowAutomation(

                trigger,

                "Production Decline Investigation",

                [

                    "Review ration",

                    "Check health records",

                    "Verify environment",

                    "Review milking process"

                ],

                "HIGH"

            )


        return WorkflowAutomation(

            trigger,

            "General Farm Review",

            [

                "Review condition"

            ],

            "MEDIUM"

        )
