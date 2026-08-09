from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4



@dataclass
class OperationalAction:
    """
    Action item generated for farm operations users.

    Represents a human-facing operational task.
    """


    action_id: str = field(
        default_factory=lambda: str(uuid4())
    )


    title: str = ""


    priority: str = "normal"


    assigned_to: str = ""


    source: str = ""


    status: str = "open"


    created_at: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )



    def complete(
        self,
    ):

        self.status = "completed"
