from dairyos.intelligence.events.services.enterprise_event_service import (
    EnterpriseEventService,
)


def test_enterprise_event_service_creation():

    service = EnterpriseEventService()


    event = service.create_event(
        event_type="service_event",
        source="runtime",
        actor="dairyos",
        entity_type="cycle",
        entity_id="cycle-001",
        payload={
            "status": "completed",
        },
    )


    assert event.event_type == "service_event"

    assert event.source == "runtime"

    assert event.payload["status"] == "completed"



def test_enterprise_event_service_correlation():

    service = EnterpriseEventService()


    event = service.create_event(
        event_type="correlation_test",
        source="runtime",
        actor="system",
        entity_type="cycle",
        entity_id="001",
        payload={},
        correlation_id="corr-001",
    )


    assert event.correlation_id == "corr-001"
