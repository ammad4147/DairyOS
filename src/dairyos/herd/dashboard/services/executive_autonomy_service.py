from ..models.executive_autonomy import ExecutiveAutonomy



class ExecutiveAutonomyService:



    def generate_brief(

        self,

        issue

    ):


        if (

            "milk" in issue.lower()

            or

            "production" in issue.lower()

        ):


            return ExecutiveAutonomy(

                "STABLE",

                issue,

                "MEDIUM",

                "Feed efficiency review",

                "Approve ration review workflow",

                "Production recovery opportunity"

            )



        return ExecutiveAutonomy(

            "STABLE",

            issue,

            "LOW",

            "Routine monitoring",

            "Review operational status",

            "Maintain performance"

        )
