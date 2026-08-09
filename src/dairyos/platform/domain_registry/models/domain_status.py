from enum import Enum


class DomainStatus(str, Enum):

    ACTIVE = "active"

    DEGRADED = "degraded"

    OFFLINE = "offline"

