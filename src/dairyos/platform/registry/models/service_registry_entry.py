from dataclasses import dataclass
from typing import Any

from dairyos.platform.container.models.service_lifecycle import ServiceLifecycle


@dataclass
class ServiceRegistryEntry:
    """
    Represents a registered runtime service.
    """

    name: str

    instance: Any

    lifecycle: ServiceLifecycle = ServiceLifecycle.REGISTERED
