from dairyos.platform.governance.models.governance_policy import GovernancePolicy


class GovernanceService:

    def __init__(self):
        self.policies = {}

    def register_policy(self, policy: GovernancePolicy):
        self.policies[policy.policy_id] = policy
        return policy

    def get_policy(self, policy_id: str):
        return self.policies.get(policy_id)

    def list_policies(self):
        return list(self.policies.values())
