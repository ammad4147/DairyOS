from dairyos.feed.events import FeedEvent


class FeedOperationsBridge:


    def __init__(self):

        self.events = []


    def publish(
        self,
        event: FeedEvent,
    ):

        self.events.append(event)


    def get_events(self):

        return self.events


    def get_events_by_type(
        self,
        event_type: str,
    ):

        return [
            event
            for event in self.events
            if event.event_type == event_type
        ]
