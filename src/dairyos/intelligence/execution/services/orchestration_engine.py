from __future__ import annotations

from dairyos.intelligence.execution.models.execution_plan import ExecutionPlan
from dairyos.intelligence.execution.models.execution_queue import ExecutionQueue
from dairyos.intelligence.execution.models.execution_task import ExecutionTask
from dairyos.intelligence.operations.orchestration.gateway.operations_orchestration_gateway import (
    OperationsOrchestrationGateway,
)


class OrchestrationEngine:
    """
    Compatibility facade over the canonical operations-orchestration gateway.

    This legacy intelligence-layer entry point prepares the established
    planning/task/queue projections without constructing a second execution
    service graph. Actual operational execution remains owned by the
    canonical operations execution boundary.
    """

    def __init__(
        self,
        orchestration_gateway: OperationsOrchestrationGateway | None = None,
    ):
        self.orchestration_gateway = (
            orchestration_gateway
            if orchestration_gateway is not None
            else OperationsOrchestrationGateway()
        )

    def orchestrate(
        self,
        workflow_type: str,
        objective: str,
        priority: str,
        task_name: str,
        assigned_to: str,
        queue_name: str,
    ):
        """Preserve the established orchestration contract."""
        action = self.orchestration_gateway.create_action(
            action_type=workflow_type,
            description=objective,
            priority=priority,
            source_decision=workflow_type,
        )

        assignment = self.orchestration_gateway.assign_action(
            action_type=workflow_type,
            assigned_to=assigned_to,
            assigned_role="operations",
        )

        plan = ExecutionPlan(
            workflow_type=workflow_type,
            objective=objective,
            priority=priority,
            status="planned",
        )

        task = ExecutionTask(
            workflow_type=workflow_type,
            task_name=task_name,
            assigned_to=assigned_to,
            status="assigned",
        )

        queue = ExecutionQueue(
            workflow_type=workflow_type,
            queue_name=queue_name,
            pending_tasks=1,
            status="active",
        )

        return {
            "plan": plan,
            "task": task,
            "queue": queue,
            "action": action,
            "assignment": assignment,
        }
