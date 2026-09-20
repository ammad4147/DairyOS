
from ..models.governance_rule import GovernanceRule


class GovernanceService:
    """
    Maintains operational governance rules.
    """

    def __init__(self):
        self.rules: list[GovernanceRule] = []


    def register_rule(
        self,
        rule: GovernanceRule,
    ) -> GovernanceRule:

        self.rules.append(rule)

        return rule


    def get_rules(self) -> list[GovernanceRule]:

        return list(self.rules)
