from dairyos.farm.operations.models import (
    MilkRecord,
    FeedRecord,
    HealthObservation,
    BreedingRecord,
)

from dairyos.farm.operations.repositories.adapters import (
    MemoryMilkRepository,
    MemoryFeedRepository,
    MemoryHealthRepository,
    MemoryBreedingRepository,
)



def test_milk_repository():

    repo = MemoryMilkRepository()

    record = MilkRecord(
        animal_group="Group A",
        shift="morning",
        litres=200,
        operator="worker",
    )

    repo.save(record)

    assert len(repo.get_all()) == 1



def test_feed_repository():

    repo = MemoryFeedRepository()

    repo.save(
        FeedRecord(
            animal_group="Group A",
            feed_type="silage",
            quantity_kg=100,
            cost=20000,
            operator="worker",
        )
    )

    assert len(repo.get_all()) == 1



def test_health_repository():

    repo = MemoryHealthRepository()

    repo.save(
        HealthObservation(
            animal_id="HF-01",
            observation="fever",
            severity="high",
            reported_by="worker",
        )
    )

    assert len(repo.get_all()) == 1



def test_breeding_repository():

    repo = MemoryBreedingRepository()

    repo.save(
        BreedingRecord(
            animal_id="HF-02",
            event_type="AI",
            result="pending",
            technician="AI tech",
        )
    )

    assert len(repo.get_all()) == 1
