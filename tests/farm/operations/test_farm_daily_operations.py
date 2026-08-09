from dairyos.farm.operations.models.milk_record import (
    MilkRecord,
)

from dairyos.farm.operations.models.feed_record import (
    FeedRecord,
)

from dairyos.farm.operations.models.health_observation import (
    HealthObservation,
)

from dairyos.farm.operations.services import (
    MilkOperationService,
    FeedOperationService,
    HealthObservationService,
)



def test_daily_farm_operations_create_events():


    milk_event = MilkOperationService().record(

        MilkRecord(
            animal_id="cow-101",
            litres=12,
            shift="morning",
            operator="worker",
        )
    )


    assert milk_event.event_type == (
        "milk_recorded"
    )


    feed_event = FeedOperationService().record(

        FeedRecord(
            group_name="milking_cows",
            feed_type="TMR",
            quantity_kg=350,
            operator="worker",
        )
    )


    assert feed_event.event_type == (
        "feed_distributed"
    )


    health_event = HealthObservationService().record(

        HealthObservation(
            animal_id="cow-104",
            observation_type="low_milk",
            notes="Production dropped",
            operator="worker",
        )
    )


    assert health_event.event_type == (
        "health_observation_recorded"
    )
