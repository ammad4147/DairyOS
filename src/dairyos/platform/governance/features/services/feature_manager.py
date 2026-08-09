from dairyos.platform.governance.features.services.feature_flag_registry import (
    FeatureFlagRegistry,
)



class FeatureManager:
    """
    Runtime feature decision service.
    """



    def __init__(
        self,
        registry: FeatureFlagRegistry,
    ):

        self.registry = registry



    def is_enabled(
        self,
        feature_key: str,
    ):

        return self.registry.enabled(
            feature_key
        )
