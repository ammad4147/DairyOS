from typing import Any, Dict

from dairyos.platform.container.models.service_lifecycle import ServiceLifecycle
from dairyos.platform.registry.models.service_registry_entry import ServiceRegistryEntry


class ServiceRegistry:
    """
    Central registry for DairyOS runtime services.
    """

    def __init__(self):
        self._services: Dict[str, ServiceRegistryEntry] = {}

    def register(self, name: str, instance: Any) -> None:
        self._services[name] = ServiceRegistryEntry(
            name=name,
            instance=instance,
            lifecycle=ServiceLifecycle.REGISTERED,
        )

    def resolve(self, name: str) -> Any:
        entry = self._services.get(name)

        if entry is None:
            raise KeyError(
                f"Service '{name}' is not registered"
            )

        return entry.instance

    def start(self, name: str) -> None:
        entry = self._services[name]
        entry.lifecycle = ServiceLifecycle.STARTED

    def stop(self, name: str) -> None:
        entry = self._services[name]
        entry.lifecycle = ServiceLifecycle.STOPPED

    def list_services(self):
        return list(self._services.values())
