from dairyos.intelligence.events.models.enterprise_event import (
    EnterpriseEvent,
)

from dairyos.intelligence.events.services.event_persistence_bridge import (
    EventPersistenceBridge,
)


def test_event_persistence_bridge_persists_enterprise_event():

    bridge = EventPersistenceBridge()


    event = EnterpriseEvent(
        event_type="test_event",
        source="test_source",
        actor="system",
        entity_type="test_entity",
        entity_id="entity-001",
        payload={
            "value": 1,
        },
    )


    stored = bridge.persist(
        event
    )


    assert stored.event_type == (
        "test_event"
    )

    assert stored.source == (
        "test_source"
    )

    assert stored.payload["entity_id"] == (
        "entity-001"
    )
