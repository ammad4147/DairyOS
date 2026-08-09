from ..models.owner_brief import OwnerBrief



class OwnerBriefService:



    def generate(

        self,

        farm_name,

        issue,

        risk_level,

        recommendation,

        confidence

    ):


        if risk_level in (

            "CRITICAL",

            "HIGH"

        ):

            status = "ATTENTION REQUIRED"

            owner_action = "Review and act on recommendation"

        else:

            status = "STABLE"

            owner_action = "Continue monitoring"



        return OwnerBrief(

            farm_name,

            status,

            issue,

            risk_level,

            recommendation,

            owner_action,

            confidence

        )



    def format_summary(

        self,

        brief

    ):


        return (

            f"{brief.farm_name}\n"

            f"Status: {brief.status}\n"

            f"Issue: {brief.primary_issue}\n"

            f"Action: {brief.owner_action}"

        )
