from dairyos.farm.production.milk.models.milk_record import (
    MilkRecord,
)

from dairyos.farm.production.milk.repository.milk_repository import (
    MilkRepository,
)

from dairyos.farm.production.milk.dashboard.milk_dashboard_service import (
    MilkDashboardService,
)



def test_milk_dashboard_summary():


    repository = MilkRepository()


    repository.save(

        MilkRecord(

            record_id="001",

            animal_id="HF-001",

            milking_session="morning",

            litres=25,

            recorded_by="worker",
        )
    )


    repository.save(

        MilkRecord(

            record_id="002",

            animal_id="HF-002",

            milking_session="morning",

            litres=20,

            recorded_by="worker",
        )
    )


    dashboard = MilkDashboardService(
        repository
    )


    summary = dashboard.daily_summary()


    assert summary["milk_litres"] == 45

    assert summary["animals_milked"] == 2

    assert (
        summary["average_litres_per_animal"]
        == 22.5
    )

    assert summary["status"] == "normal"
