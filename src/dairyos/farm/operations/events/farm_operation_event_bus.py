from dairyos.farm.operations.models.farm_operation_event import (
    FarmOperationEvent,
)


class FarmOperationEventBus:
    """
    Local domain event bus.

    The event bus is the single fan-out point for
    FarmOperationEvent delivery.

    Subscribers own projection/application behavior.
    Producers only publish events.

    Subscriber failures are isolated so one failed
    projection cannot stop the remaining event pipeline.
    """

    def __init__(self):
        self.subscribers = []
        self.failures = []

    def subscribe(self, subscriber):
        """
        Register a subscriber exactly once.
        """

        if subscriber not in self.subscribers:
            self.subscribers.append(subscriber)

        return subscriber

    def publish(self, event: FarmOperationEvent):
        """
        Publish an operational event to all subscribers.

        The producer does not invoke projections directly.
        """

        for subscriber in tuple(self.subscribers):
            try:
                subscriber.handle(event)

            except Exception as exc:
                self.failures.append(
                    {
                        "subscriber":
                            subscriber.__class__.__name__,

                        "event_type":
                            getattr(
                                event,
                                "event_type",
                                None,
                            ),

                        "event_id":
                            getattr(
                                event,
                                "event_id",
                                None,
                            ),

                        "error":
                            str(exc),
                    }
                )

        return event

    def get_failures(self):
        return list(self.failures)

    def clear_failures(self):
        self.failures.clear()
