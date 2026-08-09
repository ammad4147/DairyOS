from dairyos.farm.nutrition.feed.models.feed_record import (
    FeedRecord,
)



class FeedRepository:
    """
    Temporary feed storage.

    Later replaced by database adapter.
    """



    def __init__(
        self,
    ):

        self.records = []



    def save(
        self,
        record: FeedRecord,
    ):

        self.records.append(
            record
        )

        return record



    def get_all(
        self,
    ):

        return self.records
