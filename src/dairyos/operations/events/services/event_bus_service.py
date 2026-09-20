from collections.abc import Callable

from ..models.operational_event import OperationalEvent


class EventBusService:
    """
    Central operational event distribution service.
    """


    def __init__(self):

        self.events: list[OperationalEvent] = []
        self.subscribers: list[Callable] = []


    def publish(
        self,
        event: OperationalEvent,
    ):

        self.events.append(event)

        for subscriber in self.subscribers:
            subscriber(event)

        return event


    def subscribe(
        self,
        handler: Callable,
    ):

        self.subscribers.append(handler)

        return handler


    def history(self):

        return self.events
