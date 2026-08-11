from types import SimpleNamespace

import pytest

from dairyos.operations.execution.events.execution_event_bridge import (
    ExecutionEventBridge,
)
from dairyos.platform.events.models.operational_event import (
    OperationalEvent,
)


def test_execution_event_bridge_adapts_completed_event():
    event = SimpleNamespace(
        name="OPERATIONAL_EXECUTION_COMPLETED",
        payload={
            "execution_id": "EX-001",
            "completed_by": "worker-01",
            "notes": "Completed",
        },
    )

    result = ExecutionEventBridge().adapt(event)

    assert isinstance(result, OperationalEvent)
    assert result.event_type == "OPERATIONAL_EXECUTION_COMPLETED"
    assert result.entity_type == "execution"
    assert result.entity_id == "EX-001"
    assert result.actor == "worker-01"
    assert result.payload == event.payload


def test_execution_event_bridge_copies_payload():
    payload = {
        "execution_id": "EX-002",
        "assigned_to": "worker-02",
    }

    event = SimpleNamespace(
        name="OPERATIONAL_EXECUTION_ASSIGNED",
        payload=payload,
    )

    result = ExecutionEventBridge().adapt(event)

    assert result.payload == payload
    assert result.payload is not payload


def test_execution_event_bridge_actor_precedence():
    event = SimpleNamespace(
        name="OPERATIONAL_EXECUTION_VERIFIED",
        payload={
            "execution_id": "EX-003",
            "completed_by": "worker-01",
            "verified_by": "supervisor-01",
        },
    )

    result = ExecutionEventBridge().adapt(event)

    assert result.actor == "worker-01"


def test_execution_event_bridge_system_actor_fallback():
    event = SimpleNamespace(
        name="OPERATIONAL_EXECUTION_CREATED",
        payload={
            "execution_id": "EX-004",
        },
    )

    result = ExecutionEventBridge().adapt(event)

    assert result.actor == "SYSTEM"


@pytest.mark.parametrize(
    "event",
    [
        None,
        SimpleNamespace(name=None, payload={}),
        SimpleNamespace(
            name="OPERATIONAL_EXECUTION_COMPLETED",
            payload={},
        ),
    ],
)
def test_execution_event_bridge_rejects_invalid_event(event):
    with pytest.raises(ValueError):
        ExecutionEventBridge().adapt(event)
