from dairyos.farm.operations.events.farm_operation_event_bus import (
    FarmOperationEventBus,
)

from dairyos.farm.operations.events.operational_state_event_subscriber import (
    OperationalStateEventSubscriber,
)

from dairyos.farm.operations.models.farm_operation_event import (
    FarmOperationEvent,
)

from dairyos.farm.operations.runtime.farm_operations_runtime import (
    FarmOperationsRuntime,
)

from dairyos.farm.operations.state.farm_operational_state_service import (
    FarmOperationalStateService,
)


class CountingOperationalStateService(
    FarmOperationalStateService
):

    def __init__(self):
        super().__init__()
        self.processed_events = []

    def process_event(self, event):

        self.processed_events.append(
            event
        )

        return super().process_event(
            event
        )


def test_farm_operations_runtime_does_not_directly_subscribe_state_service():

    bus = FarmOperationEventBus()

    state_service = (
        CountingOperationalStateService()
    )

    runtime = FarmOperationsRuntime(
        event_bus=bus,
    )

    subscriber = OperationalStateEventSubscriber(
        state_service
    )

    bus.subscribe(
        subscriber
    )

    assert state_service not in bus.subscribers

    assert subscriber in bus.subscribers

    assert runtime.event_bus is bus


def test_operational_state_has_single_bus_subscription():

    bus = FarmOperationEventBus()

    state_service = (
        CountingOperationalStateService()
    )

    subscriber = (
        OperationalStateEventSubscriber(
            state_service
        )
    )

    bus.subscribe(
        subscriber
    )

    bus.subscribe(
        subscriber
    )

    assert bus.subscribers == [
        subscriber
    ]


def test_milk_event_reaches_operational_state_once():

    bus = FarmOperationEventBus()

    state_service = (
        CountingOperationalStateService()
    )

    subscriber = (
        OperationalStateEventSubscriber(
            state_service
        )
    )

    bus.subscribe(
        subscriber
    )

    event = FarmOperationEvent(
        event_type="milk_recorded",
        animal_id="COW-BATCH1-001",
        operator="worker",
        payload={
            "shift": "morning",
            "litres": 25,
        },
    )

    bus.publish(
        event
    )

    assert len(
        state_service.processed_events
    ) == 1

    state = (
        state_service.get_state()
    )

    assert (
        state.milk_status["morning"]["status"]
        == "completed"
    )

    assert (
        state.milk_status["morning"]["litres"]
        == 25
    )


def test_runtime_publishes_through_shared_bus():

    bus = FarmOperationEventBus()

    state_service = (
        CountingOperationalStateService()
    )

    subscriber = (
        OperationalStateEventSubscriber(
            state_service
        )
    )

    bus.subscribe(
        subscriber
    )

    runtime = FarmOperationsRuntime(
        event_bus=bus,
    )

    runtime.record_feed(
        animal_group="MILKING",
        feed_type="TMR",
        quantity_kg=500,
        cost=100000,
        operator="worker",
    )

    assert len(
        state_service.processed_events
    ) == 1

    state = (
        state_service.get_state()
    )

    assert (
        state.feeding_status["TMR"]["status"]
        == "completed"
    )

    assert (
        state.feeding_status["TMR"]["quantity_kg"]
        == 500
    )
