from datetime import date

from dairyos.application.dashboard.integrations.domain_dashboard_adapter import (
    DomainDashboardAdapter,
)

from dairyos.farm.operations.services.farm_operations_service import (
    FarmOperationsService,
)

from dairyos.farm.operations.repositories.adapters.memory_milk_repository import (
    MemoryMilkRepository,
)

from dairyos.farm.operations.repositories.adapters.memory_feed_repository import (
    MemoryFeedRepository,
)

from dairyos.farm.operations.models.milk_record import (
    MilkRecord,
)

from dairyos.farm.operations.models.feed_record import (
    FeedRecord,
)

from dairyos.farm.herd.repository.animal_repository import (
    AnimalRepository,
)

from dairyos.farm.herd.models.animal import (
    Animal,
)


def build_adapter():

    milk_repo = MemoryMilkRepository()
    feed_repo = MemoryFeedRepository()

    operations = FarmOperationsService(
        milk_repository=milk_repo,
        feed_repository=feed_repo,
    )

    animals = AnimalRepository()

    return (
        DomainDashboardAdapter(
            operations_service=operations,
            animal_repository=animals,
        ),
        milk_repo,
        feed_repo,
        animals,
    )


def test_empty_dashboard_returns_zero():

    adapter, _, _, _ = build_adapter()

    assert adapter.get_milk_total() == 0
    assert adapter.get_feed_consumption() == 0
    assert adapter.get_total_animals() == 0


def test_dashboard_reads_milk():

    adapter, milk_repo, _, _ = build_adapter()

    milk_repo.save(
        MilkRecord(
            litres=100,
            shift="morning",
            operator="Ahmed",
        )
    )

    assert adapter.get_milk_total() == 100


def test_dashboard_reads_feed():

    adapter, _, feed_repo, _ = build_adapter()

    feed_repo.save(
        FeedRecord(
            group_name="Milking Group",
            feed_type="TMR",
            quantity_kg=250,
            cost=5000,
            operator="Ahmed",
        )
    )

    assert adapter.get_feed_consumption() == 250


def test_dashboard_reads_herd_status():

    adapter, _, _, animals = build_adapter()

    animals.save(
        Animal(
            animal_id="1",
            tag_number="A001",
            breed="HF",
            gender="female",
            birth_date=date(2024,1,1),
            status="active",
            is_milking=True,
        )
    )

    animals.save(
        Animal(
            animal_id="2",
            tag_number="A002",
            breed="HF",
            gender="female",
            birth_date=date(2024,1,1),
            status="dry",
            is_milking=False,
        )
    )


    assert adapter.get_total_animals() == 2
    assert adapter.get_milking_animals() == 1
    assert adapter.get_dry_animals() == 1
