from dairyos.platform.events.models.operational_event import (
    OperationalEvent,
)



class EventStore:
    """
    Stores operational events.

    First persistence boundary for
    DairyOS operational history.
    """

    def __init__(self):

        self.events = []



    def append(
        self,
        event: OperationalEvent,
    ):

        self.events.append(
            event
        )

        return event



    def all(self):

        return list(
            self.events
        )



    def count(self):

        return len(
            self.events
        )
