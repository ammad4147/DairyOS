from dairyos.platform.composition.services.composition_registry import (
    CompositionRegistry,
)


class RuntimeCompositionEngine:
    """
    Builds the DairyOS enterprise runtime.
    """

    def __init__(
        self,
        registry: CompositionRegistry,
    ):

        self.registry = registry


    def compose(self):

        modules = self.registry.active_modules()

        return {
            "runtime_ready": True,
            "module_count": len(modules),
            "modules": [
                module.name
                for module in modules
            ],
        }
