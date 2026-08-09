from typing import List


class OperationalControlQueryService:
    """
    Provides operational governance control visibility.

    Read-side projection only.

    Does not:
    - enforce rules
    - trigger escalation
    - modify governance records
    """


    def build_projection(
        self,
        governance_rules: List | None = None,
        escalation_policies: List | None = None,
        review_cycles: List | None = None,
    ):

        governance_rules = (
            governance_rules
            if governance_rules is not None
            else []
        )

        escalation_policies = (
            escalation_policies
            if escalation_policies is not None
            else []
        )

        review_cycles = (
            review_cycles
            if review_cycles is not None
            else []
        )


        escalation_required = sum(

            1

            for rule in governance_rules

            if getattr(
                rule,
                "escalation_required",
                False,
            )

        )


        return {

            "control_rules":
                len(governance_rules),

            "control_escalation_policies":
                len(escalation_policies),

            "control_review_cycles":
                len(review_cycles),

            "control_escalation_required":
                escalation_required,

            "control_status":
                (
                    "ATTENTION"
                    if escalation_required > 0
                    else "NORMAL"
                ),

        }
