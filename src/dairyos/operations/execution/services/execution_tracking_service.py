from __future__ import annotations

from dairyos.operations.execution.events.execution_event_bridge import (
    ExecutionEventBridge,
)
from dairyos.operations.execution.events.execution_events import (
    ExecutionEvents,
)
from dairyos.operations.execution.models.operational_execution import (
    OperationalExecution,
)


class ExecutionTrackingService:
    """
    Application service for the authoritative OperationalExecution aggregate.

    Responsibilities:

    - invoke lifecycle operations on OperationalExecution;
    - persist lifecycle domain events when a journal is supplied;
    - translate lifecycle events into enterprise OperationalEvents;
    - publish the translated event when an event publisher is supplied.

    OperationalExecution remains the single lifecycle authority.
    """

    def __init__(
        self,
        event_publisher=None,
        event_journal=None,
    ):
        self.event_publisher = event_publisher
        self.event_journal = event_journal
        self.bridge = ExecutionEventBridge()

    def _publish_event(self, event):
        """
        Persist first, then publish.

        Persistence must succeed before downstream subscribers are allowed to
        act on the transition. This preserves the same domain-before-event
        safety boundary used elsewhere in DairyOS.
        """

        if self.event_journal is not None:
            self.event_journal.append(event)

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
        execution.assign()

        self._publish_event(
            ExecutionEvents.assigned(execution)
        )

        return execution

    def acknowledge(
        self,
        execution: OperationalExecution,
        actor: str,
    ) -> OperationalExecution:
        execution.acknowledge(actor)

        self._publish_event(
            ExecutionEvents.acknowledged(execution)
        )

        return execution

    def start(
        self,
        execution: OperationalExecution,
        actor: str | None = None,
    ) -> OperationalExecution:
        execution.start(actor)

        self._publish_event(
            ExecutionEvents.started(execution)
        )

        return execution

    def complete(
        self,
        execution: OperationalExecution,
        notes: str | None = None,
        actor: str | None = None,
    ) -> OperationalExecution:
        execution.complete(notes, actor)

        self._publish_event(
            ExecutionEvents.completed(execution)
        )

        return execution

    def verify(
        self,
        execution: OperationalExecution,
        actor: str | None = None,
    ) -> OperationalExecution:
        execution.verify(actor)

        self._publish_event(
            ExecutionEvents.verified(execution)
        )

        return execution

    def close(
        self,
        execution: OperationalExecution,
    ) -> OperationalExecution:
        execution.close()

        self._publish_event(
            ExecutionEvents.closed(execution)
        )

        return execution
