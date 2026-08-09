class TimelineService:
    """
    Command Center operational timeline.
    """



    def __init__(self):

        self.events = []



    def record(
        self,
        event,
    ):


        self.events.append(event)


        return event



    def latest(
        self,
        limit=10,
    ):


        return self.events[-limit:]



    def entity_timeline(
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

