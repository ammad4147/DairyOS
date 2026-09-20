
from ..models.escalation_policy import EscalationPolicy


class EscalationService:
    """
    Handles operational escalation policies.
    """

    def __init__(self):
        self.policies: list[EscalationPolicy] = []


    def register_policy(
        self,
        policy: EscalationPolicy,
    ) -> EscalationPolicy:

        self.policies.append(policy)

        return policy


    def get_policies(self) -> list[EscalationPolicy]:

        return list(self.policies)
