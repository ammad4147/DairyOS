from ..models.operational_execution import OperationalExecution

from ..events.execution_events import (
    ExecutionEvents,
)

from ..events.execution_event_bridge import (
    ExecutionEventBridge,
)


class ExecutionTrackingService:
    """
    Application service for the authoritative OperationalExecution
    aggregate.

    Responsibilities:

    - invoke lifecycle operations on OperationalExecution
    - translate execution lifecycle events into enterprise
      OperationalEvents when an event publisher is supplied
    - preserve the established execution-service API

    The service does NOT own execution state transitions.

    Authoritative flow:

        ExecutionTrackingService
                  |
                  v
        OperationalExecution
                  |
                  v
        ExecutionEvents
                  |
                  v
        ExecutionEventBridge
                  |
                  v
        OperationalEventPublisher

    OperationalExecution remains the single authoritative execution
    aggregate.
    """

    def __init__(
        self,
        event_publisher=None,
    ):
        self.event_publisher = event_publisher
        self.bridge = ExecutionEventBridge()

    def _publish_event(
        self,
        event,
    ):
        """
        Publish an execution event through the enterprise boundary.

        When no publisher is configured, preserve the historical
        behavior by returning the original execution event.

        When a publisher is configured:

            ExecutionEvent
                    |
                    v
            ExecutionEventBridge
                    |
                    v
            OperationalEvent
                    |
                    v
            publisher.publish()

        The adapted OperationalEvent is returned.
        """

        if self.event_publisher is None:
            return event

        operational_event = self.bridge.adapt(event)

        self.event_publisher.publish(
            operational_event
        )

        return operational_event

    def assign(
        self,
        execution: OperationalExecution,
    ) -> OperationalExecution:
        """
        Assign an execution and publish its lifecycle event.
        """

        execution.assign()

        self._publish_event(
            ExecutionEvents.assigned(
                execution
            )
        )

        return execution

    def acknowledge(
        self,
        execution: OperationalExecution,
        actor: str,
    ) -> OperationalExecution:
        """
        Acknowledge an execution by an identified actor.
        """

        execution.acknowledge(
            actor
        )

        self._publish_event(
            ExecutionEvents.acknowledged(
                execution
            )
        )

        return execution

    def start(
        self,
        execution: OperationalExecution,
        actor: str | None = None,
    ) -> OperationalExecution:
        """
        Start execution.

        OperationalExecution owns validation of the lifecycle
        transition, including established compatibility paths.
        """

        execution.start(
            actor
        )

        self._publish_event(
            ExecutionEvents.started(
                execution
            )
        )

        return execution

    def complete(
        self,
        execution: OperationalExecution,
        notes: str | None = None,
        actor: str | None = None,
    ) -> OperationalExecution:
        """
        Complete execution and optionally record notes and actor.
        """

        execution.complete(
            notes,
            actor,
        )

        self._publish_event(
            ExecutionEvents.completed(
                execution
            )
        )

        return execution

    def verify(
        self,
        execution: OperationalExecution,
        actor: str | None = None,
    ) -> OperationalExecution:
        """
        Verify completed execution.
        """

        execution.verify(
            actor
        )

        self._publish_event(
            ExecutionEvents.verified(
                execution
            )
        )

        return execution

    def close(
        self,
        execution: OperationalExecution,
    ) -> OperationalExecution:
        """
        Close a verified execution.
        """

        execution.close()

        self._publish_event(
            ExecutionEvents.closed(
                execution
            )
        )

        return execution
