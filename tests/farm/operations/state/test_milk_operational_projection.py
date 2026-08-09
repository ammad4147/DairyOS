from dairyos.farm.operations.events.farm_operation_event_bus import (
    FarmOperationEventBus,
)

from dairyos.farm.operations.events.operational_state_event_subscriber import (
    OperationalStateEventSubscriber,
)

from dairyos.farm.operations.runtime.farm_operations_runtime import (
    FarmOperationsRuntime,
)

from dairyos.farm.operations.state.farm_operational_state_service import (
    FarmOperationalStateService,
)

from dairyos.farm.operations.services.operational_state_query_service import (
    OperationalStateQueryService,
)


def _build_runtime():
    state_service = FarmOperationalStateService()

    event_bus = FarmOperationEventBus()

    subscriber = OperationalStateEventSubscriber(
        state_service
    )

    event_bus.subscribe(
        subscriber
    )

    runtime = FarmOperationsRuntime(
        event_bus=event_bus
    )

    return runtime, state_service


def test_milk_event_updates_live_operational_state():

    runtime, state_service = _build_runtime()

    runtime.record_milk(
        animal_group="Milking Cows",
        shift="Morning",
        litres=280,
        operator="worker",
    )

    state = state_service.get_state()

    assert state.milk_status["Morning"]["litres"] == 280

    assert (
        state.milk_status["Morning"]["status"]
        == "completed"
    )


def test_multiple_animals_accumulate_milk_projection():

    runtime, state_service = _build_runtime()

    runtime.record_milk(
        animal_id="HF-001",
        shift="Morning",
        litres=15,
        operator="worker1",
    )

    runtime.record_milk(
        animal_id="HF-002",
        shift="Morning",
        litres=20,
        operator="worker2",
    )

    state = state_service.get_state()

    assert (
        state.milk_status["Morning"]["litres"]
        == 35
    )

    assert (
        state.milk_status["Morning"]["animals_milked"]
        == 2
    )


def test_milk_projection_retains_operator_accountability():

    runtime, state_service = _build_runtime()

    runtime.record_milk(
        animal_id="HF-003",
        shift="Evening",
        litres=18,
        operator="Milker-A",
    )

    state = state_service.get_state()

    assert (
        "Milker-A"
        in state.milk_status["Evening"]["operators"]
    )


def test_operational_query_exposes_live_milk_projection():

    runtime, state_service = _build_runtime()

    runtime.record_milk(
        animal_id="HF-010",
        shift="Morning",
        litres=25,
        operator="worker",
    )

    query = OperationalStateQueryService(
        state_service
    )

    read_model = query.get_current_state()

    assert read_model.milk_total == 25

    assert (
        read_model.milk_status["Morning"]["litres"]
        == 25
    )
