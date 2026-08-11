from dairyos.operations.execution.services.operational_execution_service import (
    OperationalExecutionService,
)

from dairyos.operations.execution.services.execution_lifecycle_bridge import (
    ExecutionLifecycleBridge,
)


class ExecutionLifecycleEventHandler:
    """
    Handles enterprise operational-execution lifecycle events.

    Authoritative execution aggregate:
        OperationalExecution

    Responsibility:
        OperationalEvent
            |
            v
        resolve OperationalExecution
            |
            v
        ExecutionLifecycleBridge

    This handler does not:
    - mutate execution lifecycle state
    - publish events
    - own execution lifecycle rules

    Compatibility contract:
    - existing ApplicationRuntime construction is preserved
    - existing ExecutionEventSubscriber construction is preserved
    - existing event names are preserved
    - existing OperationalExecution lookup is preserved
    - existing ExecutionLifecycleBridge calls are preserved
    """

    COMPLETED_EVENT = "OPERATIONAL_EXECUTION_COMPLETED"
    VERIFIED_EVENT = "OPERATIONAL_EXECUTION_VERIFIED"

    HANDLED_EVENTS = {
        COMPLETED_EVENT,
        VERIFIED_EVENT,
    }

    def __init__(
        self,
        execution_service: OperationalExecutionService,
        lifecycle_bridge: ExecutionLifecycleBridge | None = None,
    ):
        if execution_service is None:
            raise ValueError(
                "ExecutionLifecycleEventHandler requires OperationalExecutionService"
            )

        self.execution_service = execution_service

        self.lifecycle_bridge = (
            lifecycle_bridge
            if lifecycle_bridge is not None
            else ExecutionLifecycleBridge()
        )

    def handle(
        self,
        operational_event,
    ):
        """
        Consume an enterprise operational execution event.

        Unsupported events are deliberately ignored so that this
        subscriber remains safe when attached to the broader
        FarmOperationEventBus.
        """

        event_type = operational_event.event_type

        if event_type not in self.HANDLED_EVENTS:
            return None

        execution_id = operational_event.entity_id

        execution = self.execution_service.get_execution(
            execution_id
        )

        if execution is None:
            raise ValueError(
                f"Execution not found: {execution_id}"
            )

        if event_type == self.COMPLETED_EVENT:
            return self.lifecycle_bridge.record_execution_outcome(
                execution=execution,
                impact_score=0,
                notes=execution.notes or "",
            )

        if event_type == self.VERIFIED_EVENT:
            return self.lifecycle_bridge.verify_execution(
                execution=execution,
                success=True,
                message="Execution verified",
            )

        return None
