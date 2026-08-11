from dairyos.farm.operations.runtime.farm_operations_runtime import (
    FarmOperationsRuntime,
)

from dairyos.farm.operations.events.farm_operation_event_bus import (
    FarmOperationEventBus,
)


class FakePublisher:

    def __init__(self):
        self.events = []

    def publish(
        self,
        event,
    ):
        self.events.append(
            event
        )

        return event


def test_runtime_publishes_one_enterprise_event_per_farm_event():
    publisher = FakePublisher()

    runtime = FarmOperationsRuntime(
        event_bus=FarmOperationEventBus(),
        operational_event_publisher=publisher,
    )

    runtime.record_feed(
        animal_group="MILKING",
        feed_type="TMR",
        quantity_kg=500,
        cost=100000,
        operator="worker-01",
    )

    assert len(
        publisher.events
    ) == 1

    event = publisher.events[0]

    assert (
        event.event_type
        == "feed_distributed"
    )

    assert (
        event.entity_type
        == "farm_operation"
    )

    assert (
        event.actor
        == "worker-01"
    )
