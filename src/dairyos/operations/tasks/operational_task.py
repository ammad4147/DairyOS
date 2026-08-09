from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4



@dataclass
class OperationalTask:
    """
    Represents a real farm operational task.

    Routed through TaskDispatcher
    and executed by task handlers.
    """


    task_type: str


    task_name: str


    entity_id: str


    assigned_to: str


    status: str = "pending"


    task_id: str = field(
        default_factory=lambda: str(uuid4())
    )


    created_at: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )


    completed_at: datetime | None = None



    def complete(
        self,
    ):

        self.status = "completed"


        self.completed_at = datetime.now(
            timezone.utc
        )

