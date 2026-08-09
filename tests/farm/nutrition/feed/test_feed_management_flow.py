from dairyos.farm.nutrition.feed.models.feed_record import (
    FeedRecord,
)

from dairyos.farm.nutrition.feed.repository.feed_repository import (
    FeedRepository,
)

from dairyos.farm.nutrition.feed.services.feed_management_service import (
    FeedManagementService,
)



def test_daily_feed_recording():


    service = FeedManagementService(

        FeedRepository()

    )


    service.record_feed(

        FeedRecord(

            record_id="FEED-001",

            feed_type="TMR",

            quantity_kg=500,

            cost_per_kg=60,

            animal_group="milking_cows",

            recorded_by="worker",
        )
    )


    assert (
        service.total_feed_kg()
        == 500
    )


    assert (
        service.total_feed_cost()
        == 30000
    )
