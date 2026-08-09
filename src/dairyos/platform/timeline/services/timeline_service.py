from dairyos.platform.timeline.models.timeline_event import (
    TimelineEvent,
)



class TimelineService:
    """
    Operational event history service.
    """



    def __init__(self):

        self.events = []



    def record(
        self,
        event: TimelineEvent,
    ):

        self.events.append(event)

        return event



    def history(
        self,
        entity_type,
        entity_id,
    ):


        return [

            event

            for event in self.events

            if (

                event.entity_type == entity_type

                and

                event.entity_id == entity_id

            )

        ]



    def latest(
        self,
        entity_type,
        entity_id,
    ):


        records = self.history(

            entity_type,

            entity_id,

        )


        return records[-1] if records else None

