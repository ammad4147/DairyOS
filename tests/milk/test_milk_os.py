from dairyos.milk import (
    MilkRecord,
    MilkingSession,
    MilkRecordService,
)


def test_create_milk_record():

    record = MilkRecord(
        record_id="MR-001",
        animal_id="HF-001",
        session=MilkingSession.MORNING,
        quantity_litres=12.5,
        operator="Ali",
    )

    assert record.quantity_litres == 12.5



def test_daily_milk_total():

    service = MilkRecordService()

    service.add_record(
        MilkRecord(
            record_id="MR-001",
            animal_id="HF-001",
            session=MilkingSession.MORNING,
            quantity_litres=10,
            operator="Ali",
        )
    )

    service.add_record(
        MilkRecord(
            record_id="MR-002",
            animal_id="HF-002",
            session=MilkingSession.MORNING,
            quantity_litres=15,
            operator="Ali",
        )
    )


    assert service.daily_total() == 25



def test_animal_yield():

    service = MilkRecordService()

    service.add_record(
        MilkRecord(
            record_id="MR-003",
            animal_id="HF-001",
            session=MilkingSession.EVENING,
            quantity_litres=8,
            operator="Ali",
        )
    )

    assert service.animal_daily_yield(
        "HF-001"
    ) == 8
