from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class OperationalAssignment:
    """
    Connects an operational user
    with an operational action.
    """

    user_id: str

    action_id: str

    assignment_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    status: str = "assigned"

    assigned_at: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )


    def complete(
        self,
    ):

        self.status = "completed"
