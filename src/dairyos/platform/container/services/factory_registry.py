from typing import Callable, Any


class FactoryRegistry:
    """
    Stores runtime factories for dynamic service creation.
    """

    def __init__(self):

        self._factories = {}


    def register_factory(
        self,
        name: str,
        factory: Callable[[], Any],
    ):

        self._factories[name] = factory


    def create(
        self,
        name: str,
    ):

        factory = self._factories.get(name)

        if factory is None:
            raise KeyError(
                f"Factory '{name}' not registered"
            )


        return factory()


    def list_factories(self):

        return list(
            self._factories.keys()
        )
