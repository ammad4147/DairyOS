from ..models.event import DairyEvent


class EventPublisher:

    def __init__(self):

        self.events = []


    def publish(self, event: DairyEvent):

        self.events.append(event)

        return event
