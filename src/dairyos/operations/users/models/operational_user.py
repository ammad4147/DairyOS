from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


from dairyos.operations.users.operational_role import (
    OperationalRole,
)


@dataclass
class OperationalUser:
    """
    Represents a farm operational user.
    """

    name: str

    role: OperationalRole

    user_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    active: bool = True

    created_at: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )


    def deactivate(
        self,
    ):

        self.active = False
