from dataclasses import dataclass, field
from datetime import datetime, timezone

from .action_status import ActionStatus
from .action_assignment import ActionAssignment


@dataclass
class OperationalAction:
    """
    Represents an executable operational task.

    Actions are operational commitments.
    They are created from operational needs,
    assigned to responsible persons,
    tracked through lifecycle states,
    and projected into Farm Operational State.
    """

    action_id: str

    title: str

    description: str

    assignment: ActionAssignment

    status: ActionStatus

    priority: str = "NORMAL"

    source_event_id: str | None = None

    source_decision_id: str | None = None

    created_by_system: bool = True

    due_date: datetime | None = None

    created_at: datetime = field(
        default_factory=lambda:
        datetime.now(timezone.utc)
    )
