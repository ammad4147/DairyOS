from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class OperationalExecution:
    """
    Authoritative DairyOS operational execution aggregate.

    This is the single source of truth for the lifecycle of an
    operational action that has actually been executed.

    Canonical lifecycle:

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

    Compatibility paths are deliberately supported because existing
    DairyOS callers historically invoke start() or complete() directly
    on a newly-created execution.

    Compatibility does NOT create a second lifecycle authority.
    All state transitions remain centralized in _transition().
    """

    CREATED = "CREATED"
    ASSIGNED = "ASSIGNED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    STARTED = "STARTED"
    COMPLETED = "COMPLETED"
    VERIFIED = "VERIFIED"
    CLOSED = "CLOSED"

    # ------------------------------------------------------------------
    # Authoritative lifecycle transition table
    # ------------------------------------------------------------------
    #
    # The normal lifecycle is:
    #
    # CREATED -> ASSIGNED -> ACKNOWLEDGED -> STARTED
    #         -> COMPLETED -> VERIFIED -> CLOSED
    #
    # Existing callers, however, legitimately use:
    #
    # CREATED -> STARTED
    # CREATED -> COMPLETED
    #
    # and some legacy flows complete directly from ASSIGNED or
    # ACKNOWLEDGED. Those paths are therefore retained explicitly.
    #
    _TRANSITIONS = {
        CREATED: {
            ASSIGNED,
            ACKNOWLEDGED,
            STARTED,
            COMPLETED,
        },
        ASSIGNED: {
            ACKNOWLEDGED,
            STARTED,
            COMPLETED,
        },
        ACKNOWLEDGED: {
            STARTED,
            COMPLETED,
        },
        STARTED: {
            COMPLETED,
        },
        COMPLETED: {
            VERIFIED,
            CLOSED,
        },
        VERIFIED: {
            CLOSED,
        },
        CLOSED: set(),
    }

    execution_id: str
    action_id: str
    assigned_to: str

    status: str = CREATED

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

    # ------------------------------------------------------------------
    # Internal authoritative transition mechanism
    # ------------------------------------------------------------------

    def _transition(self, new_status: str) -> None:
        """
        Apply one authoritative lifecycle transition.

        No execution service is permitted to maintain a competing
        lifecycle state machine. Every aggregate state transition
        passes through this method.
        """

        allowed = self._TRANSITIONS.get(
            self.status,
            set(),
        )

        if new_status not in allowed:
            raise ValueError(
                "Invalid operational execution transition: "
                f"{self.status} -> {new_status}"
            )

        self.status = new_status

    # ------------------------------------------------------------------
    # Lifecycle operations
    # ------------------------------------------------------------------

    def assign(self) -> None:
        self._transition(self.ASSIGNED)

        self.assigned_at = datetime.now()

    def acknowledge(
        self,
        actor: str,
    ) -> None:

        self._transition(self.ACKNOWLEDGED)

        self.acknowledged_at = datetime.now()
        self.acknowledged_by = actor

    def start(
        self,
        actor: Optional[str] = None,
    ) -> None:

        self._transition(self.STARTED)

        self.started_at = datetime.now()
        self.started_by = actor

    def complete(
        self,
        notes: Optional[str] = None,
        actor: Optional[str] = None,
    ) -> None:

        self._transition(self.COMPLETED)

        self.completed_at = datetime.now()
        self.completed_by = actor
        self.notes = notes

    def verify(
        self,
        actor: Optional[str] = None,
    ) -> None:

        self._transition(self.VERIFIED)

        self.verified_at = datetime.now()
        self.verified_by = actor

    def close(self) -> None:

        self._transition(self.CLOSED)

        self.closed_at = datetime.now()

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def is_completed(self) -> bool:
        return self.status in {
            self.COMPLETED,
            self.VERIFIED,
            self.CLOSED,
        }

    def is_verified(self) -> bool:
        return self.status in {
            self.VERIFIED,
            self.CLOSED,
        }

    def is_closed(self) -> bool:
        return self.status == self.CLOSED
