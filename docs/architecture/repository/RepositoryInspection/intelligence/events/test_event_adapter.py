from dairyos.intelligence.events.adapters.event_adapter import (
    EventAdapter,
)

from dairyos.intelligence.events.models.enterprise_event import (
    EnterpriseEvent,
)



def test_event_adapter_conversion():

    event = EnterpriseEvent(
        event_type="adapter_test",
        source="runtime",
        actor="system",
        entity_type="decision",
        entity_id="decision-001",
        payload={
            "approved": True,
        },
    )


    adapter = EventAdapter()


    result = adapter.adapt(
        event
    )


    assert result["event_type"] == "adapter_test"

    assert result["entity_id"] == "decision-001"

    assert result["payload"]["approved"] is True
