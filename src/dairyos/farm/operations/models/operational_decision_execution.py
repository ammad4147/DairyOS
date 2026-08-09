from dataclasses import dataclass, field
from datetime import datetime, UTC
from uuid import uuid4


@dataclass
class OperationalDecisionExecution:
    """
    Represents an approved execution attempt
    for an operational decision.

    Decisions remain recommendations.
    Execution requires explicit approval.

    This object records execution governance,
    not operational truth.
    """

    decision_id: str

    action: str

    approved_by: str

    status: str = "PENDING"

    result: dict | str | None = None

    execution_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    completed_at: datetime | None = None


    def approve(
        self,
    ):

        self.status = "APPROVED"


    def complete(
        self,
        result=None,
    ):

        self.status = "EXECUTED"

        self.result = result

        self.completed_at = (
            datetime.now(UTC)
        )


    def fail(
        self,
        result=None,
    ):

        self.status = "FAILED"

        self.result = result

        self.completed_at = (
            datetime.now(UTC)
        )


    def reject(
        self,
        result=None,
    ):

        self.status = "REJECTED"

        self.result = result

        self.completed_at = (
            datetime.now(UTC)
        )


    def to_dict(
        self,
    ):

        return {

            "execution_id":
                self.execution_id,

            "decision_id":
                self.decision_id,

            "action":
                self.action,

            "approved_by":
                self.approved_by,

            "status":
                self.status,

            "result":
                self.result,

            "created_at":
                self.created_at.isoformat(),

            "completed_at":
                (
                    self.completed_at.isoformat()
                    if self.completed_at
                    else None
                ),

        }
