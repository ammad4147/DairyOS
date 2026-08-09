from typing import List

from ..models.governance_rule import GovernanceRule


class GovernanceService:
    """
    Maintains operational governance rules.
    """

    def __init__(self):
        self.rules: List[GovernanceRule] = []


    def register_rule(
        self,
        rule: GovernanceRule,
    ) -> GovernanceRule:

        self.rules.append(rule)

        return rule


    def get_rules(self) -> List[GovernanceRule]:

        return list(self.rules)
