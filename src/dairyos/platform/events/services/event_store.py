from dairyos.platform.events.models.operational_event import (
    OperationalEvent,
)


class EventStore:
    """
    Enterprise operational-event persistence boundary.

    The EventStore remains the platform-facing persistence abstraction.

    Production composition may supply an OperationalEventRepository,
    in which case events are persisted through the repository.

    Tests and compatibility callers may omit the repository and retain
    the existing in-memory behavior.
    """

    def __init__(
        self,
        repository=None,
    ):
        self.repository = repository
        self.events = []

    def append(
        self,
        event: OperationalEvent,
    ):
        if event is None:
            raise ValueError(
                "OperationalEvent is required."
            )

        if self.repository is not None:
            return self.repository.add(
                event
            )

        self.events.append(
            event
        )

        return event

    def all(self):
        if self.repository is not None:
            getter = getattr(
                self.repository,
                "get_all",
                None,
            )

            if callable(getter):
                return list(
                    getter()
                )

        return list(
            self.events
        )

    def count(self):
        if self.repository is not None:
            counter = getattr(
                self.repository,
                "count",
                None,
            )

            if callable(counter):
                return counter()

        return len(
            self.events
        )
