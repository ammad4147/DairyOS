from dairyos.farm.operations.models import (
    MilkRecord,
    FeedRecord,
    HealthObservation,
    BreedingRecord,
)



def test_milk_record_creation():

    record = MilkRecord(
        animal_group="Lactating Group A",
        shift="morning",
        litres=250,
        operator="farm_manager",
    )

    assert record.litres == 250



def test_feed_record_creation():

    record = FeedRecord(
        animal_group="Lactating Group A",
        feed_type="silage",
        quantity_kg=400,
        cost=80000,
        operator="worker",
    )

    assert record.quantity_kg == 400



def test_health_observation_creation():

    observation = HealthObservation(
        animal_id="HF-104",
        observation="Reduced appetite",
        severity="medium",
        reported_by="worker",
    )

    assert observation.animal_id == "HF-104"



def test_breeding_record_creation():

    record = BreedingRecord(
        animal_id="HF-121",
        event_type="AI",
        result="pending",
        technician="AI technician",
    )

    assert record.event_type == "AI"
