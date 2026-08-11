from dairyos.farm.operations.gateway.operations_event_gateway import (
    OperationsEventGateway,
)

from dairyos.farm.operations.events.farm_operation_event_bridge import (
    FarmOperationEventBridge,
)

from dairyos.farm.operations.gateway.operational_event_adapter import (
    OperationalEventAdapter,
)

from dairyos.farm.operations.models.farm_operation_event import (
    FarmOperationEvent,
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


def test_canonical_farm_event_bridge_translates_event():
    event = FarmOperationEvent(
        event_type="milk_recorded",
        animal_id="COW-001",
        operator="worker-01",
        payload={
            "litres": 25,
        },
    )

    result = FarmOperationEventBridge().adapt(
        event
    )

    assert result.event_type == "milk_recorded"
    assert result.entity_type == "animal"
    assert result.entity_id == "COW-001"
    assert result.actor == "worker-01"
    assert result.payload == {
        "litres": 25,
    }


def test_legacy_operational_event_adapter_uses_canonical_bridge():
    adapter = OperationalEventAdapter()

    assert isinstance(
        adapter,
        FarmOperationEventBridge,
    )


def test_gateway_publishes_exactly_one_operational_event():
    publisher = FakePublisher()

    gateway = OperationsEventGateway(
        operational_event_publisher=publisher,
    )

    event = FarmOperationEvent(
        event_type="feed_distributed",
        animal_id=None,
        operator="worker-01",
        payload={
            "quantity_kg": 500,
        },
    )

    gateway.publish(
        event
    )

    assert len(
        publisher.events
    ) == 1

    operational_event = (
        publisher.events[0]
    )

    assert (
        operational_event.event_type
        == "feed_distributed"
    )

    assert (
        operational_event.entity_type
        == "farm_operation"
    )

    assert (
        operational_event.actor
        == "worker-01"
    )
