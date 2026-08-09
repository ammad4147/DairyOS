from dairyos.platform.governance.rules.services.governance_rule_registry import (
    GovernanceRuleRegistry,
)



class ComplianceChecker:
    """
    Evaluates governance rule availability.
    """



    def __init__(
        self,
        registry: GovernanceRuleRegistry,
    ):

        self.registry = registry



    def evaluate(
        self,
        rule_key: str,
    ):

        rule = self.registry.get(
            rule_key
        )


        if rule is None:

            return {
                "compliant": False,
                "reason": "Rule not registered",
            }



        return {
            "compliant": rule.enabled,
            "rule": rule.key,
        }
