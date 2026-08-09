from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class Permission:
    """
    Defines an allowed enterprise capability.
    """

    name: str

    permission_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    resource: str = ""

    action: str = ""

    description: str = ""

    active: bool = True
