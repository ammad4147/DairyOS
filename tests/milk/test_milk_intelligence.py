from dairyos.milk.models import (
    MilkEntry,
    MilkingSession,
)

from dairyos.milk.intelligence import (
    MilkPerformanceService,
    MilkAlertService,
    MilkAnomalyService,
)



def create_entries():

    return [

        MilkEntry(
            entry_id="M001",
            animal_id="HF-001",
            session=MilkingSession.MORNING,
            litres=15,
            operator="Worker",
        ),

        MilkEntry(
            entry_id="M002",
            animal_id="HF-002",
            session=MilkingSession.EVENING,
            litres=10,
            operator="Worker",
        ),

    ]



def test_milk_performance_summary():

    result = MilkPerformanceService().summarize(
        create_entries()
    )


    assert result["total_litres"] == 25

    assert result["animals_milked"] == 2



def test_missing_milk_alert():

    result = MilkAlertService().missing_entry_alert(
        20,
        25
    )


    assert result["severity"] == "HIGH"



def test_milk_drop_detection():

    result = MilkAnomalyService().detect_drop(
        "HF-001",
        30,
        15
    )


    assert result["anomaly"] == "MILK_DROP"

    assert result["severity"] == "HIGH"
