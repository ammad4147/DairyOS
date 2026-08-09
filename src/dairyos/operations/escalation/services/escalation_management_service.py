from typing import List


class EscalationManagementService:
    """
    Manages operational escalations.
    """


    def __init__(self):

        self.escalations: List = []


    def create_escalation(
        self,
        escalation,
    ):

        self.escalations.append(escalation)

        return escalation


    def active_escalations(self):

        return [
            item
            for item in self.escalations
            if not item.resolved
        ]
