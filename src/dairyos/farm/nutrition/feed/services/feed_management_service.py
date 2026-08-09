from dairyos.farm.nutrition.feed.models.feed_record import (
    FeedRecord,
)



class FeedManagementService:
    """
    Handles daily feed recording.
    """



    def __init__(
        self,
        repository,
    ):

        self.repository = repository



    def record_feed(
        self,
        record: FeedRecord,
    ):

        return self.repository.save(
            record
        )



    def total_feed_kg(
        self,
    ):

        return sum(

            record.quantity_kg

            for record

            in self.repository.get_all()

        )



    def total_feed_cost(
        self,
    ):

        return sum(

            record.quantity_kg
            *
            record.cost_per_kg

            for record

            in self.repository.get_all()

        )
