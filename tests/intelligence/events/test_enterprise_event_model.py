from datetime import datetime

from dairyos.intelligence.events.models.enterprise_event import (
    EnterpriseEvent,
)


def test_enterprise_event_creation():

    event = EnterpriseEvent(
        event_type="test_event",
        source="test_source",
        actor="test_actor",
        entity_type="test_entity",
        entity_id="entity-001",
        payload={
            "value": 1,
        },
    )


    assert event.event_type == "test_event"

    assert event.source == "test_source"

    assert event.entity_id == "entity-001"

    assert event.payload["value"] == 1



def test_enterprise_event_identity():

    event = EnterpriseEvent(
        event_type="identity_test",
        source="test",
        actor="tester",
        entity_type="sample",
        entity_id="001",
        payload={},
    )


    assert event.event_id is not None

    assert event.correlation_id is not None



def test_enterprise_event_timestamp():

    event = EnterpriseEvent(
        event_type="time_test",
        source="test",
        actor="tester",
        entity_type="sample",
        entity_id="001",
        payload={},
    )


    assert isinstance(
        event.timestamp,
        datetime,
    )
