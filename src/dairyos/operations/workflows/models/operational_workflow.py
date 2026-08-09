from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4



@dataclass
class OperationalWorkflow:
    """
    Tracks lifecycle of operational work.

    Represents the journey of a farm activity
    from creation to completion.
    """


    task_id: str


    workflow_type: str


    assigned_to: str


    status: str = "created"


    workflow_id: str = field(
        default_factory=lambda: str(uuid4())
    )


    created_at: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )


    started_at: datetime | None = None


    completed_at: datetime | None = None



    def start(
        self,
    ):

        self.status = "started"


        self.started_at = datetime.now(
            timezone.utc
        )



    def complete(
        self,
    ):

        self.status = "completed"


        self.completed_at = datetime.now(
            timezone.utc
        )

