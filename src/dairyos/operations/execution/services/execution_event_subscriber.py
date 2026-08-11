from dairyos.operations.execution.services.execution_lifecycle_event_handler import (
    ExecutionLifecycleEventHandler,
)


class ExecutionEventSubscriber:
    """
    Routes enterprise execution lifecycle events to the
    execution lifecycle event handler.

    Authoritative flow:

        OperationalExecution
                |
                v
        ExecutionTrackingService
                |
                v
        ExecutionEvent
                |
                v
        ExecutionEventBridge
                |
                v
        FarmOperationEvent / OperationalEvent
                |
                v
        ExecutionEventSubscriber
                |
                v
        ExecutionLifecycleEventHandler
                |
                v
        ExecutionLifecycleBridge

    Responsibilities
    ----------------
    This subscriber:

    - identifies execution lifecycle events
    - forwards supported events to the lifecycle handler
    - ignores unrelated events
    - preserves dependency-injection compatibility

    This subscriber does NOT:

    - own execution state
    - mutate OperationalExecution directly
    - define lifecycle rules
    - create outcomes
    - perform verification
    - assess closure
    - publish events

    The lifecycle handler and lifecycle bridge remain authoritative
    for downstream execution consequences.
    """

    EXECUTION_EVENTS = frozenset(
        {
            ExecutionLifecycleEventHandler.COMPLETED_EVENT,
            ExecutionLifecycleEventHandler.VERIFIED_EVENT,
        }
    )

    def __init__(
        self,
        handler: ExecutionLifecycleEventHandler | None = None,
        execution_service=None,
    ):
        """
        Construct the execution event subscriber.

        Preferred contract:
            handler=<ExecutionLifecycleEventHandler>

        Compatibility contract:
            execution_service=<OperationalExecutionService>

        At least one dependency must be supplied.

        A supplied handler always takes precedence over the
        compatibility execution_service argument.
        """

        if handler is not None:
            self.handler = handler
            return

        if execution_service is not None:
            self.handler = ExecutionLifecycleEventHandler(
                execution_service=execution_service,
            )
            return

        raise ValueError(
            "ExecutionEventSubscriber requires execution lifecycle handler"
        )

    def handle(
        self,
        event,
    ):
        """
        Route a supported execution lifecycle event.

        Unsupported events are deliberately ignored so this
        subscriber remains safe when registered on the shared
        FarmOperationEventBus.
        """

        event_type = getattr(
            event,
            "event_type",
            None,
        )

        if event_type not in self.EXECUTION_EVENTS:
            return None

        return self.handler.handle(
            event
        )
