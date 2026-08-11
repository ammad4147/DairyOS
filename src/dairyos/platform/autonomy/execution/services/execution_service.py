from dairyos.platform.autonomy.execution.models.action_plan import (
    ActionPlan,
)


class ExecutionService:
    """
    Controls autonomous action planning and approval.

    This service does not own operational execution state.

    Canonical boundary:

        autonomous intelligence
                |
                v
            ActionPlan
                |
             approval
                v
        OperationalAction
                |
                v
        OperationalExecution

    ``OperationalExecution`` is the only authoritative operational
    execution aggregate in DairyOS.
    """

    PLAN_DRAFT = "draft"
    PLAN_PENDING_APPROVAL = "pending_approval"
    PLAN_APPROVED = "approved"
    PLAN_REJECTED = "rejected"

    def create_plan(
        self,
        title,
        description,
        assigned_to,
        priority,
    ):
        return ActionPlan(
            title=title,
            description=description,
            assigned_to=assigned_to,
            priority=priority,
            status=self.PLAN_DRAFT,
        )

    def approve(
        self,
        plan,
    ):
        """Approve a plan for hand-off to operational action creation."""

        if plan.status not in {
            self.PLAN_DRAFT,
            self.PLAN_PENDING_APPROVAL,
        }:
            raise ValueError(
                f"Cannot approve ActionPlan from status {plan.status!r}."
            )

        plan.status = self.PLAN_APPROVED
        return plan

    def reject(
        self,
        plan,
    ):
        """Reject a plan without creating operational execution state."""

        if plan.status not in {
            self.PLAN_DRAFT,
            self.PLAN_PENDING_APPROVAL,
        }:
            raise ValueError(
                f"Cannot reject ActionPlan from status {plan.status!r}."
            )

        plan.status = self.PLAN_REJECTED
        return plan

    def complete(
        self,
        plan,
    ):
        """
        Legacy compatibility operation.

        A planning object cannot become ``completed``. Actual completion
        belongs exclusively to OperationalExecution. Existing callers may
        continue invoking this method during migration; it therefore
        normalizes the plan to the approved hand-off state instead of
        introducing a second execution lifecycle.
        """

        if plan.status in {
            self.PLAN_DRAFT,
            self.PLAN_PENDING_APPROVAL,
        }:
            plan.status = self.PLAN_APPROVED

        if plan.status != self.PLAN_APPROVED:
            raise ValueError(
                f"ActionPlan cannot be handed off from status {plan.status!r}."
            )

        return plan
