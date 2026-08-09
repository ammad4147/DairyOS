"""
DairyOS Execution Gateway

Enterprise execution access boundary.

Supports:

- legacy autonomous task execution
- enterprise workflow execution
- backward compatibility
"""


class ExecutionGateway:

    def __init__(
        self,
        coordinator=None,
    ):

        if coordinator is None:

            from dairyos.intelligence.execution.services.execution_coordinator import (
                ExecutionCoordinator,
            )

            coordinator = ExecutionCoordinator()

        self.coordinator = coordinator


    def execute(
        self,
        task=None,
        workflow_type=None,
        objective=None,
        priority=None,
        task_name=None,
        assigned_to=None,
        queue_name=None,
    ):

        if not hasattr(
            self.coordinator,
            "execute",
        ):

            return None


        #
        # Legacy compatibility path
        #
        if (
            task is not None
            and workflow_type is None
            and objective is None
            and priority is None
            and task_name is None
            and assigned_to is None
            and queue_name is None
        ):

            return self.coordinator.execute(
                task=task
            )


        #
        # Enterprise execution path
        #
        return self.coordinator.execute(
            task=task,
            workflow_type=workflow_type,
            objective=objective,
            priority=priority,
            task_name=task_name,
            assigned_to=assigned_to,
            queue_name=queue_name,
        )


    def get_coordinator(
        self,
    ):

        return self.coordinator
