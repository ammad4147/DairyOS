from dairyos.farm.operations.runtime import (
    FarmOperationsRuntime,
)



def test_daily_farm_operations_create_records():

    runtime = FarmOperationsRuntime()


    runtime.record_milk(
        animal_group="Milking Cows",
        shift="Morning",
        litres=280,
        operator="worker",
    )


    runtime.record_feed(
        animal_group="Milking Cows",
        feed_type="Silage",
        quantity_kg=500,
        cost=50000,
        operator="worker",
    )


    runtime.record_health(
        animal_id="HF-101",
        observation="Reduced appetite",
        severity="medium",
        reported_by="worker",
    )


    assert len(
        runtime.milk_repository.get_all()
    ) == 1


    assert len(
        runtime.feed_repository.get_all()
    ) == 1


    assert len(
        runtime.health_repository.get_all()
    ) == 1
