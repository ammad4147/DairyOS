from ..models.animal_health_baseline import AnimalHealthBaseline



class AnimalBaselineService:



    def create(

        self,

        animal_id,

        milk_yield,

        feed_intake,

        temperature,

        activity,

        days

    ):

        return AnimalHealthBaseline(

            animal_id,

            milk_yield,

            feed_intake,

            temperature,

            activity,

            days

        )
