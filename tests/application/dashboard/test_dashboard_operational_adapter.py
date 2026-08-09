from dairyos.application.dashboard.integrations.domain_dashboard_adapter import (
    DomainDashboardAdapter,
)

from dairyos.farm.operations.repositories.adapters.memory_milk_repository import (
    MemoryMilkRepository,
)

from dairyos.farm.operations.models.milk_record import (
    MilkRecord,
)


def test_dashboard_reads_milk_from_repository():

    repository = MemoryMilkRepository()


    repository.save(
        MilkRecord(
            animal_group="Milking Herd",
            litres=250,
            shift="morning",
            operator="Ahmed",
        )
    )


    adapter = DomainDashboardAdapter(
        milk_repository=repository
    )


    assert (
        adapter.get_milk_total()
        == 250
    )
