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


def test_milk_production_intelligence_reflects_verified_milk():

    runtime, state_service = _build_runtime()

    runtime.record_milk(
        animal_id="Milking Cows",
        shift="Morning",
        litres=280,
        operator="worker",
    )

    query = OperationalStateQueryService(
        state_service
    )

    result = query.get_current_state()

    intelligence = (
        result.milk_production_intelligence
    )

    assert intelligence["total_litres"] == 280

    assert (
        intelligence["production_status"]
        in (
            "VERIFIED",
            "INCOMPLETE",
        )
    )


def test_milk_production_intelligence_tracks_shift_output():

    runtime, state_service = _build_runtime()

    runtime.record_milk(
        animal_id="Milking Cows",
        shift="Morning",
        litres=280,
        operator="worker",
    )

    runtime.record_milk(
        animal_id="Milking Cows",
        shift="Evening",
        litres=240,
        operator="worker",
    )

    query = OperationalStateQueryService(
        state_service
    )

    intelligence = (
        query.get_current_state()
        .milk_production_intelligence
    )

    assert (
        intelligence["shift_production"]["Morning"]
        == 280
    )

    assert (
        intelligence["shift_production"]["Evening"]
        == 240
    )

    assert intelligence["total_litres"] == 520


def test_missing_milk_checkpoint_is_detected():

    state_service = FarmOperationalStateService()

    query = OperationalStateQueryService(
        state_service
    )

    intelligence = (
        query.get_current_state()
        .milk_production_intelligence
    )

    assert (
        "missing_checkpoints"
        in intelligence
    )


def test_operational_query_exposes_milk_intelligence():

    runtime, state_service = _build_runtime()

    runtime.record_milk(
        animal_id="HF-001",
        shift="Morning",
        litres=25,
        operator="worker",
    )

    read_model = (
        OperationalStateQueryService(
            state_service
        )
        .get_current_state()
    )

    assert (
        read_model.milk_production_intelligence
        is not None
    )

    assert (
        read_model.milk_production_intelligence[
            "total_litres"
        ]
        == 25
    )
