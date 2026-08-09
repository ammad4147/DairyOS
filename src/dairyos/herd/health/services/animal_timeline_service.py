class AnimalTimelineService:



    def __init__(self):

        self.events = []



    def add_event(

        self,

        event

    ):

        self.events.append(event)

        return event



    def get_timeline(

        self,

        animal_id

    ):

        return [

            event

            for event in self.events

            if event.animal_id == animal_id

        ]



    def count_events(

        self,

        animal_id

    ):

        return len(

            self.get_timeline(animal_id)

        )
