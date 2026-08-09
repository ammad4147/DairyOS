from dairyos.platform.autonomy.governance.models.safety_check import (
    SafetyCheck,
)



class AutonomyGovernance:
    """
    Controls autonomous decision execution.
    """



    def evaluate(

        self,

        confidence,

        risk_level,

    ):


        if confidence < 0.75:

            return SafetyCheck(

                allowed=False,

                reason="Confidence below threshold",

            )


        if risk_level == "high":

            return SafetyCheck(

                allowed=False,

                reason="Human approval required",

            )


        return SafetyCheck(

            allowed=True,

            reason="Approved by policy",

        )

