from typing import List

from ..models.automation_rule import AutomationRule


class AutomationRuleService:
    """
    Stores and manages operational automation rules.
    """


    def __init__(self):

        self.rules: List[AutomationRule] = []


    def register_rule(
        self,
        rule: AutomationRule,
    ):

        self.rules.append(rule)

        return rule


    def active_rules(self):

        return [
            rule
            for rule in self.rules
            if rule.enabled
        ]
