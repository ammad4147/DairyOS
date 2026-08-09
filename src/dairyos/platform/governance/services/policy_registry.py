from typing import Dict


from dairyos.platform.governance.models.platform_policy import (
    PlatformPolicy,
)



class PolicyRegistry:
    """
    Stores enterprise governance policies.
    """


    def __init__(self):

        self._policies: Dict[str, PlatformPolicy] = {}



    def register(
        self,
        policy: PlatformPolicy,
    ):

        self._policies[
            policy.name
        ] = policy



    def get(
        self,
        name: str,
    ):

        return self._policies.get(name)



    def all(self):

        return list(
            self._policies.values()
        )
