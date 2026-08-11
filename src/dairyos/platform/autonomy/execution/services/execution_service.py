from typing import Dict

from dairyos.platform.autonomy.execution.models.action_plan import (
    ActionPlan,
)

from dairyos.operations.execution.models.operational_execution import (
    OperationalExecution,
)

from dairyos.operations.execution.services.operational_execution_service import (
    OperationalExecutionService,
)

from dairyos.operations.execution.services.execution_tracking_service import (
    ExecutionTrackingService,
)


class ExecutionService:
    """
    Autonomous planning/approval compatibility service.

    ActionPlan is a planning artifact only.

    OperationalExecution is the sole authoritative representation of
    actual operational execution.

    Canonical flow:

        ActionPlan
            |
            | approve
            v
        OperationalAction / Assignment
            |
            v
        OperationalExecution
            |
            v
        ExecutionTrackingService

    This service exists at the autonomy boundary and deliberately does
    not maintain a second execution lifecycle.
    """

    PLAN_DRAFT = "draft"
    PLAN_PENDING_APPROVAL = "pending_approval"
    PLAN_APPROVED = "approved"
    PLAN_REJECTED = "rejected"

    def __init__(
        self,
        operational_execution_service=None,
        execution_tracking_service=None,
    ):
        self.operational_execution_service = (
            operational_execution_service
            if operational_execution_service is not None
            else OperationalExecutionService()
        )

        self.execution_tracking_service = (
            execution_tracking_service
            if execution_tracking_service is not None
            else ExecutionTrackingService()
        )

        self._executions_by_plan: Dict[int, OperationalExecution] = {}

    def create_plan(
        self,
        title,
        description,
        assigned_to,
        priority,
    ):
        """
        Create an autonomous planning artifact.

        No operational execution exists at this point.
        """

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
        """
        Approve the planning artifact.

        Approval creates the hand-off into the canonical operational
        execution boundary.

        The ActionPlan itself remains ``approved``.
        """

        if plan.status not in {
            self.PLAN_DRAFT,
            self.PLAN_PENDING_APPROVAL,
        }:
            raise ValueError(
                f"Cannot approve ActionPlan from status {plan.status!r}."
            )

        plan.status = self.PLAN_APPROVED

        execution = self._get_or_create_execution(plan)

        if execution.status == OperationalExecution.CREATED:
            self.execution_tracking_service.assign(execution)

        return plan

    def reject(
        self,
        plan,
    ):
        """
        Reject the planning artifact.

        Rejection never creates or mutates operational execution state.
        """

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
        notes=None,
        actor=None,
    ):
        """
        Legacy compatibility entry point.

        ``ActionPlan`` is never marked completed.

        Instead, completion is applied to the canonical
        ``OperationalExecution``.

        Returns the canonical OperationalExecution so callers can
        observe the actual execution result.
        """

        if plan.status != self.PLAN_APPROVED:
            raise ValueError(
                "ActionPlan must be approved before operational "
                f"completion; current status is {plan.status!r}."
            )

        execution = self._get_or_create_execution(plan)

        if execution.status == OperationalExecution.CREATED:
            self.execution_tracking_service.assign(execution)

        if execution.status == OperationalExecution.ASSIGNED:
            self.execution_tracking_service.start(
                execution,
                actor=actor,
            )

        if execution.status == OperationalExecution.STARTED:
            self.execution_tracking_service.complete(
                execution,
                notes=notes,
                actor=actor,
            )

        elif execution.status == OperationalExecution.COMPLETED:
            # Idempotent compatibility behavior for callers that invoke
            # complete() more than once after successful completion.
            return execution

        elif execution.status in {
            OperationalExecution.VERIFIED,
            OperationalExecution.CLOSED,
        }:
            return execution

        else:
            raise ValueError(
                "OperationalExecution cannot be completed from status "
                f"{execution.status!r}."
            )

        return execution

    def get_execution(
        self,
        plan,
    ):
        """
        Return the canonical OperationalExecution associated with a plan.
        """

        return self._executions_by_plan.get(id(plan))

    def _get_or_create_execution(
        self,
        plan,
    ) -> OperationalExecution:
        """
        Create exactly one canonical OperationalExecution for a plan.

        The autonomy layer does not create an execution aggregate of its
        own. It delegates creation to OperationalExecutionService.
        """

        existing = self._executions_by_plan.get(id(plan))

        if existing is not None:
            return existing

        action_id = f"AUTONOMY-ACTION-{id(plan)}"

        execution = self.operational_execution_service.create_execution(
            action_id=action_id,
            assigned_to=plan.assigned_to,
        )

        self._executions_by_plan[id(plan)] = execution

        return execution
