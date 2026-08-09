from dairyos.milk import (
    MilkEntry,
    MilkService,
    MilkingSession,
)



def test_complete_milking_workflow():


    service = MilkService()


    entry = MilkEntry(

        entry_id="ME-100",

        animal_id="HF-001",

        session=MilkingSession.MORNING,

        litres=15,

        operator="Milker-1"

    )


    record = service.record_milking(
        entry
    )


    assert record.quantity_litres == 15

    assert service.daily_production() == 15



def test_animal_yield_calculation():


    service = MilkService()


    service.record_milking(

        MilkEntry(

            entry_id="ME-101",

            animal_id="HF-010",

            session=MilkingSession.MORNING,

            litres=12,

            operator="Worker"

        )

    )


    service.record_milking(

        MilkEntry(

            entry_id="ME-102",

            animal_id="HF-010",

            session=MilkingSession.EVENING,

            litres=8,

            operator="Worker"

        )

    )


    assert service.animal_yield(
        "HF-010"
    ) == 20



def test_invalid_milk_entry_rejected():


    service = MilkService()


    entry = MilkEntry(

        entry_id="ME-103",

        animal_id="HF-001",

        session=MilkingSession.MORNING,

        litres=-5,

        operator="Worker"

    )


    try:

        service.record_milking(
            entry
        )

        assert False


    except ValueError:

        assert True
