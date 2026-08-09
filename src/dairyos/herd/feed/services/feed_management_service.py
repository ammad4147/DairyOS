from ..models.feed_management import FeedManagement



class FeedManagementService:



    def evaluate(

        self,

        animal_group,

        animal_count,

        feed_per_animal,

        cost_per_animal

    ):


        total_feed = (

            animal_count *

            feed_per_animal

        )


        total_cost = (

            animal_count *

            cost_per_animal

        )


        if cost_per_animal > 2500:

            status = "MONITOR"

        else:

            status = "NORMAL"



        return FeedManagement(

            animal_group,

            animal_count,

            total_feed,

            total_cost,

            cost_per_animal,

            status

        )
