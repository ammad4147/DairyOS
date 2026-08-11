from dairyos.platform.events.models.operational_event import (
    OperationalEvent,
)


class OperationalEventPublisher:
    """
    Application/platform boundary for publishing enterprise
    operational events.

    Canonical publication flow:

        OperationalEvent
              |
              +--> persistence
              |
              +--> enterprise EventBus
              |
              +--> EventDispatcher

    The publisher owns enterprise publication orchestration.

    Persistence compatibility:

    - EventStore exposes append(event).
    - OperationalEventRepository exposes add(event).

    The publisher deliberately supports both existing contracts rather
    than forcing a persistence adapter to pretend it has an unrelated
    interface.

    The publisher does not:
    - translate farm events
    - own farm operational state
    - invoke farm-domain subscribers
    - implement business rules
    """

    def __init__(
        self,
        store,
        bus,
        dispatcher,
    ):
        if store is None:
            raise ValueError(
                "OperationalEventPublisher requires a store."
            )

        if bus is None:
            raise ValueError(
                "OperationalEventPublisher requires an event bus."
            )

        if dispatcher is None:
            raise ValueError(
                "OperationalEventPublisher requires an event dispatcher."
            )

        self.store = store
        self.bus = bus
        self.dispatcher = dispatcher

    def _persist(
        self,
        event: OperationalEvent,
    ):
        """
        Persist an operational event through the supplied persistence
        boundary.

        EventStore uses append().
        OperationalEventRepository uses add().

        The publisher intentionally prefers the canonical EventStore
        contract when available and falls back to the repository
        contract when an application composition root supplies the
        repository directly.
        """

        append = getattr(
            self.store,
            "append",
            None,
        )

        if callable(append):
            return append(event)

        add = getattr(
            self.store,
            "add",
            None,
        )

        if callable(add):
            return add(event)

        raise TypeError(
            "Operational event persistence boundary must expose "
            "append(event) or add(event)."
        )

    def publish(
        self,
        event: OperationalEvent,
    ):
        """
        Publish exactly one enterprise operational event.

        Ordering is deliberate:

            1. persist
            2. publish to enterprise EventBus
            3. dispatch to registered enterprise handlers

        Farm-domain publication remains the responsibility of the
        FarmOperationEventBus and OperationsEventGateway.
        """

        if event is None:
            raise ValueError(
                "OperationalEvent is required."
            )

        self._persist(
            event
        )

        self.bus.publish(
            event
        )

        self.dispatcher.dispatch(
            event
        )

        return event
