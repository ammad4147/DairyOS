from dairyos.farm.production.milk.models.milk_record import (
    MilkRecord,
)

from dairyos.farm.production.milk.repository.milk_repository import (
    MilkRepository,
)

from dairyos.farm.production.milk.services.milk_recording_service import (
    MilkRecordingService,
)



def test_daily_milk_recording():


    service = MilkRecordingService(
        MilkRepository()
    )


    service.record_milk(

        MilkRecord(

            record_id="MILK-001",

            animal_id="HF-001",

            milking_session="morning",

            litres=25,

            recorded_by="milker",
        )
    )


    service.record_milk(

        MilkRecord(

            record_id="MILK-002",

            animal_id="HF-002",

            milking_session="morning",

            litres=22,

            recorded_by="milker",
        )
    )


    assert service.total_milk() == 47
