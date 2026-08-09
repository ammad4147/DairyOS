from dataclasses import dataclass
from enum import Enum


class ConfigurationScope(str, Enum):
    """
    Defines configuration ownership scope.
    """

    GLOBAL = "GLOBAL"
    TENANT = "TENANT"
    FARM = "FARM"
    USER = "USER"


@dataclass
class ConfigurationItem:
    """
    Enterprise configuration definition.
    """

    key: str
    value: str
    scope: ConfigurationScope
    owner_id: str | None = None
    active: bool = True

    def is_active(self) -> bool:
        return self.active
