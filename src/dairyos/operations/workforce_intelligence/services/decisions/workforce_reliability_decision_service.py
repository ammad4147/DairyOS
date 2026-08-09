from dairyos.operations.workforce_intelligence.models.workforce_reliability_snapshot import (
    WorkforceReliabilitySnapshot,
)


class WorkforceReliabilityDecisionService:
    """
    Converts workforce reliability intelligence
    into management decisions.
    """


    def generate_decision(
        self,
        snapshot: WorkforceReliabilitySnapshot,
    ):

        if snapshot.reliability_status == "HIGH":

            return {

                "decision_status": "STABLE",

                "management_action_required": False,

                "recommended_action":
                    "Maintain workforce performance",

            }



        if snapshot.reliability_status == "MEDIUM":

            return {

                "decision_status": "MONITOR",

                "management_action_required": True,

                "recommended_action":
                    "Monitor workforce execution reliability",

            }



        return {

            "decision_status": "INTERVENTION_REQUIRED",

            "management_action_required": True,

            "recommended_action":
                "Review workforce execution failures and assign corrective action",

        }
