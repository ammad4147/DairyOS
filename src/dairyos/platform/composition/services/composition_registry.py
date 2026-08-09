from typing import List

from dairyos.platform.composition.models.composition_module import (
    CompositionModule,
)


class CompositionRegistry:
    """
    Stores modules available for runtime composition.
    """

    def __init__(self):

        self.modules: List[CompositionModule] = []


    def register(
        self,
        module: CompositionModule,
    ):

        self.modules.append(module)


    def active_modules(self):

        return [
            module
            for module in self.modules
            if module.enabled
        ]
