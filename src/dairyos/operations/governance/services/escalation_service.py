from typing import List

from ..models.escalation_policy import EscalationPolicy


class EscalationService:
    """
    Handles operational escalation policies.
    """

    def __init__(self):
        self.policies: List[EscalationPolicy] = []


    def register_policy(
        self,
        policy: EscalationPolicy,
    ) -> EscalationPolicy:

        self.policies.append(policy)

        return policy


    def get_policies(self) -> List[EscalationPolicy]:

        return list(self.policies)
