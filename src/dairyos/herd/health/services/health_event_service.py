from datetime import datetime

from ..models.health_event import HealthEvent



class HealthEventService:



    def __init__(self):

        self.events = []



    def create_event(

        self,

        animal_id,

        event_type,

        description,

        severity,

        reported_by

    ):


        event = HealthEvent(

            animal_id=animal_id,

            event_type=event_type,

            description=description,

            severity=severity,

            reported_by=reported_by,

            status="OPEN",

            created_at=datetime.utcnow()

        )


        self.events.append(event)


        return event



    def get_animal_events(

        self,

        animal_id

    ):


        return [

            event

            for event in self.events

            if event.animal_id == animal_id

        ]



    def close_event(

        self,

        event

    ):


        event.status = "CLOSED"

        return event
