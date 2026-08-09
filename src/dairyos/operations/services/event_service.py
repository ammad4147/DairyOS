from dairyos.operations.events.operational_event import (
    OperationalEvent,
)



class EventService:


    def __init__(self):

        self.events = []



    def record(

        self,

        event: OperationalEvent,

    ):

        self.events.append(event)

        return event



    def all_events(self):

        return self.events

