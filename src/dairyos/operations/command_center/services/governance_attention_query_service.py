from typing import List


class GovernanceAttentionQueryService:
    """
    Provides governance attention signals
    for Command Center visibility.

    Read-side projection only.

    Does not:
    - trigger escalation
    - assign owners
    - modify governance state
    """


    def build_projection(
        self,
        governance_rules: List | None = None,
        escalation_policies: List | None = None,
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


        escalation_required = [

            rule

            for rule in governance_rules

            if getattr(
                rule,
                "escalation_required",
                False,
            )

        ]


        return {

            "governance_attention_required":
                len(escalation_required) > 0,


            "governance_attention_count":
                len(escalation_required),


            "governance_escalation_policy_count":
                len(escalation_policies),


            "governance_attention_items":
                escalation_required,

        }
