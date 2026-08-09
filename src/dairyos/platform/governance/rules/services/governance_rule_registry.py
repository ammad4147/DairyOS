from typing import Dict


from dairyos.platform.governance.rules.models.governance_rule import (
    GovernanceRule,
)



class GovernanceRuleRegistry:
    """
    Registry for governance rules.
    """



    def __init__(self):

        self._rules: Dict[str, GovernanceRule] = {}



    def register(
        self,
        rule: GovernanceRule,
    ):

        self._rules[
            rule.key
        ] = rule



    def get(
        self,
        key: str,
    ):

        return self._rules.get(
            key
        )



    def all(self):

        return list(
            self._rules.values()
        )
