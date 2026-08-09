from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class OperationalExecution:
    """
    Represents actual execution of farm operational work.

    Lifecycle:

    CREATED
        |
        v
    ASSIGNED
        |
        v
    ACKNOWLEDGED
        |
        v
    STARTED
        |
        v
    COMPLETED
        |
        v
    VERIFIED
        |
        v
    CLOSED
    """

    execution_id: str

    action_id: str

    assigned_to: str

    status: str = "CREATED"

    assigned_at: Optional[datetime] = None

    acknowledged_at: Optional[datetime] = None

    started_at: Optional[datetime] = None

    completed_at: Optional[datetime] = None

    verified_at: Optional[datetime] = None

    closed_at: Optional[datetime] = None

    acknowledged_by: Optional[str] = None

    started_by: Optional[str] = None

    completed_by: Optional[str] = None

    verified_by: Optional[str] = None

    notes: Optional[str] = None

    created_at: datetime = field(
        default_factory=datetime.now
    )


    def assign(self) -> None:
        self.status = "ASSIGNED"
        self.assigned_at = datetime.now()


    def acknowledge(
        self,
        actor: str,
    ) -> None:

        self.status = "ACKNOWLEDGED"
        self.acknowledged_at = datetime.now()
        self.acknowledged_by = actor


    def start(
        self,
        actor: Optional[str] = None,
    ) -> None:

        self.status = "STARTED"
        self.started_at = datetime.now()
        self.started_by = actor


    def complete(
        self,
        notes: Optional[str] = None,
        actor: Optional[str] = None,
    ) -> None:

        self.status = "COMPLETED"
        self.completed_at = datetime.now()
        self.completed_by = actor
        self.notes = notes


    def verify(
        self,
        actor: Optional[str] = None,
    ) -> None:

        self.status = "VERIFIED"
        self.verified_at = datetime.now()
        self.verified_by = actor


    def close(self) -> None:

        self.status = "CLOSED"
        self.closed_at = datetime.now()


    def is_completed(self) -> bool:

        return self.status in [
            "COMPLETED",
            "VERIFIED",
            "CLOSED",
        ]
