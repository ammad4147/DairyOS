
from dataclasses import dataclass, field
from datetime import datetime

from .decision_priority import DecisionPriority


@dataclass
class OperationalDecision:
    """
    Represents an actionable operational decision.

    Lifecycle:

        CREATED
            |
            v
        ACKNOWLEDGED
            |
            v
        COMPLETED


    The decision layer records intent and accountability.

    It does not:
    - execute farm actions
    - mutate operational state
    - bypass human ownership
    """


    decision_id: str

    title: str

    description: str

    priority: DecisionPriority

    owner_action_required: bool


    status: str = "CREATED"


    owner: str | None = None


    source: str | None = None


    outcome: str | None = None


    created_at: datetime = field(
        default_factory=datetime.now
    )


    acknowledged_at: datetime | None = None


    completed_at: datetime | None = None



    def acknowledge(
        self,
        owner: str | None = None,
    ):

        self.status = "ACKNOWLEDGED"

        self.owner = owner

        self.acknowledged_at = datetime.now()



    def complete(
        self,
        outcome: str | None = None,
    ):

        self.status = "COMPLETED"

        self.outcome = outcome

        self.completed_at = datetime.now()
