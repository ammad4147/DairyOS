from typing import Dict


from dairyos.platform.governance.features.models.feature_flag import (
    FeatureFlag,
)



class FeatureFlagRegistry:
    """
    Stores platform feature configuration.
    """



    def __init__(self):

        self._flags: Dict[str, FeatureFlag] = {}



    def register(
        self,
        flag: FeatureFlag,
    ):

        self._flags[
            flag.key
        ] = flag



    def get(
        self,
        key: str,
    ):

        return self._flags.get(
            key
        )



    def enabled(
        self,
        key: str,
    ):

        flag = self.get(key)

        if flag is None:

            return False


        return flag.enabled
