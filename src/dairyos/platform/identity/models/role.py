from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


class RoleType(str, Enum):
    """
    Standard DairyOS enterprise roles.
    """

    OWNER = "OWNER"
    FARM_MANAGER = "FARM_MANAGER"
    VETERINARIAN = "VETERINARIAN"
    NUTRITIONIST = "NUTRITIONIST"
    WORKER = "WORKER"
    SYSTEM_AGENT = "SYSTEM_AGENT"


@dataclass
class Role:
    """
    Represents an authorization role
    within the DairyOS platform.
    """

    name: RoleType

    role_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    description: str = ""

    active: bool = True
