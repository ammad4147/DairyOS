from dairyos.farm.operations.models.feed_record import (
    FeedRecord,
)

from dairyos.farm.operations.models.farm_operation_event import (
    FarmOperationEvent,
)


class FeedOperationService:
    """
    Processes daily feeding activities.
    """


    def record(
        self,
        record: FeedRecord,
    ):

        return FarmOperationEvent(

            event_type="feed_distributed",

            animal_id=None,

            operator=record.operator,

            payload={
                "group_name": record.group_name,
                "feed_type": record.feed_type,
                "quantity_kg": record.quantity_kg,
            },
        )
