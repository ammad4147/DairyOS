from dairyos.farm.operations.models.milk_record import (
    MilkRecord,
)

from dairyos.farm.operations.services import (
    MilkOperationService,
    OperationsTimelineService,
)



def test_farm_event_enters_daily_timeline():


    event = MilkOperationService().record(

        MilkRecord(

            animal_id="cow-101",

            litres=14,

            shift="morning",

            operator="worker",

        )
    )


    timeline = OperationsTimelineService()


    recorded = timeline.record(
        event
    )


    assert recorded["event_type"] == (
        "milk_recorded"
    )


    assert recorded["animal_id"] == (
        "cow-101"
    )


    assert len(
        timeline.get_timeline()
    ) == 1
