from dataclasses import dataclass, field
from datetime import datetime
from typing import ClassVar


@dataclass
class ActionStatus:
    """
    Represents controlled execution status of an operational action.

    DairyOS controls lifecycle progression.

    Operational rules:
    - System creates actions in OPEN state.
    - Execution can move through IN_PROGRESS.
    - Operational completion may be recorded directly from OPEN
      when the responsible operator confirms completion.
    - Verification and closure remain controlled transitions.
    """

    status: str

    updated_at: datetime = field(
        default_factory=datetime.now
    )


    VALID_STATUSES: ClassVar[set[str]] = {
        "OPEN",
        "IN_PROGRESS",
        "COMPLETED",
        "VERIFIED",
        "CLOSED",
    }


    ALLOWED_TRANSITIONS: ClassVar[dict[str, set[str]]] = {

        "OPEN": {
            "IN_PROGRESS",
            "COMPLETED",
        },

        "IN_PROGRESS": {
            "COMPLETED",
        },

        "COMPLETED": {
            "VERIFIED",
        },

        "VERIFIED": {
            "CLOSED",
        },

        "CLOSED": set(),

    }


    def __post_init__(self):

        self.status = self.status.upper()

        if self.status not in self.VALID_STATUSES:

            raise ValueError(
                f"Invalid action status: {self.status}"
            )


    def can_transition_to(
        self,
        new_status: str,
    ) -> bool:

        new_status = new_status.upper()

        return new_status in self.ALLOWED_TRANSITIONS.get(
            self.status,
            set(),
        )


    def transition_to(
        self,
        new_status: str,
    ) -> None:

        new_status = new_status.upper()

        if not self.can_transition_to(
            new_status
        ):

            raise ValueError(
                f"Invalid transition: "
                f"{self.status} -> {new_status}"
            )


        self.status = new_status

        self.updated_at = datetime.now()
