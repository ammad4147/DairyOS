from dataclasses import dataclass


@dataclass
class ActionPlan:
    """
    Autonomous planning and approval artifact.

    ActionPlan is deliberately not an execution aggregate. Its lifecycle
    describes planning/approval only; actual farm work is represented by
    OperationalExecution.

    Allowed plan states:

        draft
        pending_approval
        approved
        rejected

    Operational execution states such as STARTED or COMPLETED must never
    be stored on this object.
    """

    PLAN_DRAFT = "draft"
    PLAN_PENDING_APPROVAL = "pending_approval"
    PLAN_APPROVED = "approved"
    PLAN_REJECTED = "rejected"

    title: str
    description: str
    assigned_to: str
    priority: str
    status: str = PLAN_DRAFT

    def __post_init__(self) -> None:
        allowed = {
            self.PLAN_DRAFT,
            self.PLAN_PENDING_APPROVAL,
            self.PLAN_APPROVED,
            self.PLAN_REJECTED,
        }

        if self.status not in allowed:
            raise ValueError(
                "Invalid ActionPlan planning status: "
                f"{self.status!r}"
            )

    @property
    def is_approved(self) -> bool:
        return self.status == self.PLAN_APPROVED

    @property
    def is_rejected(self) -> bool:
        return self.status == self.PLAN_REJECTED
