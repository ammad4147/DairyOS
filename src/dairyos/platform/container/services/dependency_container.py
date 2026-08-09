from typing import Dict, Any

from dairyos.platform.container.models.service_definition import (
    ServiceDefinition,
)


class DependencyContainer:
    """
    Enterprise dependency injection container.
    """

    def __init__(self):

        self._definitions: Dict[str, ServiceDefinition] = {}

        self._instances: Dict[str, Any] = {}


    def register(
        self,
        definition: ServiceDefinition,
    ):

        self._definitions[
            definition.name
        ] = definition


    def resolve(
        self,
        name: str,
    ):

        if name in self._instances:
            return self._instances[name]


        definition = self._definitions.get(name)

        if definition is None:
            raise KeyError(
                f"Service '{name}' not registered"
            )


        instance = definition.service_type()


        if definition.singleton:
            self._instances[name] = instance


        return instance


    def list_services(self):

        return list(
            self._definitions.keys()
        )
