from dairyos.platform.events.models.operational_event import (
    OperationalEvent,
)



class EventBus:
    """
    Operational event publication boundary.
    """

    def __init__(self):

        self.subscribers = []



    def subscribe(
        self,
        handler,
    ):

        self.subscribers.append(
            handler
        )



    def publish(
        self,
        event: OperationalEvent,
    ):

        for handler in self.subscribers:

            handler(event)


        return event
