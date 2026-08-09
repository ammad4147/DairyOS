from dataclasses import dataclass
from typing import Type


@dataclass
class ServiceDefinition:
    """
    Defines a runtime-managed service.
    """

    name: str

    service_type: Type

    singleton: bool = True
