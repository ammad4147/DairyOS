from dairyos.milk import (
    MilkEntry,
    MilkEntryService,
    MilkingSession,
)



def test_record_milk_entry():

    service = MilkEntryService()

    entry = MilkEntry(
        entry_id="ME-001",
        animal_id="HF-001",
        session=MilkingSession.MORNING,
        litres=11,
        operator="Worker-1",
    )

    service.record_entry(entry)

    assert len(service.get_entries()) == 1



def test_session_collection():

    service = MilkEntryService()


    service.record_entry(
        MilkEntry(
            entry_id="ME-002",
            animal_id="HF-001",
            session=MilkingSession.MORNING,
            litres=12,
            operator="Worker-1",
        )
    )


    service.record_entry(
        MilkEntry(
            entry_id="ME-003",
            animal_id="HF-002",
            session=MilkingSession.EVENING,
            litres=8,
            operator="Worker-1",
        )
    )


    assert service.session_total(
        MilkingSession.MORNING
    ) == 12



def test_animal_daily_total():

    service = MilkEntryService()


    service.record_entry(
        MilkEntry(
            entry_id="ME-004",
            animal_id="HF-005",
            session=MilkingSession.MORNING,
            litres=10,
            operator="Worker",
        )
    )


    assert service.animal_total(
        "HF-005"
    ) == 10
