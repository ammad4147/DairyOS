from __future__ import annotations

from typing import Any

from dairyos.intelligence.execution.services.orchestration_engine import (
    OrchestrationEngine,
)


class ExecutionCoordinator:
    """
    Compatibility/application facade for the execution orchestration boundary.

    The coordinator does not compose the execution subsystem. Composition is
    owned by the application runtime / orchestration boundary. This class
    preserves the established public ``execute`` contract for callers that
    still enter through the intelligence execution package.
    """

    def __init__(self, orchestration_engine: OrchestrationEngine | None = None):
        self.orchestration_engine = orchestration_engine or OrchestrationEngine()

    def execute(
        self,
        task: Any = None,
        workflow_type: Any = None,
        objective: Any = None,
        priority: Any = None,
        task_name: Any = None,
        assigned_to: Any = None,
        queue_name: Any = None,
    ) -> Any:
        """
        Preserve the established execution entry contract.

        A pre-built task continues to pass through unchanged when no workflow
        type is supplied. Workflow execution is delegated unchanged to the
        authoritative orchestration boundary.
        """
        if task is not None and workflow_type is None:
            return task

        return self.orchestration_engine.orchestrate(
            workflow_type=workflow_type,
            objective=objective,
            priority=priority,
            task_name=task_name,
            assigned_to=assigned_to,
            queue_name=queue_name,
        )
