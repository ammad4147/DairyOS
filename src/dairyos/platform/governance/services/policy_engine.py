from dairyos.platform.governance.services.policy_registry import (
    PolicyRegistry,
)



class PolicyEngine:
    """
    Evaluates enterprise platform policies.
    """


    def __init__(
        self,
        registry: PolicyRegistry,
    ):

        self.registry = registry



    def allowed(
        self,
        policy_name: str,
    ):

        policy = self.registry.get(
            policy_name
        )

        if policy is None:

            return False


        return policy.enabled
