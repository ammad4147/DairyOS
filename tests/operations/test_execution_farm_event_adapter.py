from types import SimpleNamespace

import pytest

from dairyos.operations.execution.events.execution_farm_event_adapter import (
    ExecutionFarmEventAdapter,
)
from dairyos.farm.operations.models.farm_operation_event import (
    FarmOperationEvent,
)


def test_execution_farm_event_adapter_converts_event():
    event = SimpleNamespace(
        name="OPERATIONAL_EXECUTION_COMPLETED",
        payload={
            "execution_id": "EX-001",
            "completed_by": "worker-01",
            "notes": "Completed",
        },
    )

    result = ExecutionFarmEventAdapter().adapt(event)

    assert isinstance(result, FarmOperationEvent)
    assert result.event_type == "OPERATIONAL_EXECUTION_COMPLETED"
    assert result.animal_id is None
    assert result.operator == "worker-01"
    assert result.payload == event.payload


def test_execution_farm_event_adapter_copies_payload():
    payload = {
        "execution_id": "EX-002",
        "completed_by": "worker-02",
    }

    event = SimpleNamespace(
        name="OPERATIONAL_EXECUTION_COMPLETED",
        payload=payload,
    )

    result = ExecutionFarmEventAdapter().adapt(event)

    assert result.payload == payload
    assert result.payload is not payload


def test_execution_farm_event_adapter_resolves_actor_priority():
    event = SimpleNamespace(
        name="OPERATIONAL_EXECUTION_VERIFIED",
        payload={
            "completed_by": "worker-01",
            "verified_by": "supervisor-01",
        },
    )

    result = ExecutionFarmEventAdapter().adapt(event)

    assert result.operator == "worker-01"


def test_execution_farm_event_adapter_falls_back_to_system():
    event = SimpleNamespace(
        name="OPERATIONAL_EXECUTION_CREATED",
        payload={
            "execution_id": "EX-003",
        },
    )

    result = ExecutionFarmEventAdapter().adapt(event)

    assert result.operator == "SYSTEM"


@pytest.mark.parametrize(
    "event",
    [
        None,
        SimpleNamespace(name=None, payload={}),
    ],
)
def test_execution_farm_event_adapter_rejects_invalid_event(event):
    with pytest.raises(ValueError):
        ExecutionFarmEventAdapter().adapt(event)
