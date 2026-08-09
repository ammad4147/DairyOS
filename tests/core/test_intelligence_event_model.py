from dairyos.intelligence.persistence.models.intelligence_event import (
    IntelligenceEvent,
)


def test_intelligence_event_creates_history_record():

    event = IntelligenceEvent(
        event_type="signal_received",
        source="health",
        payload={
            "severity": "critical",
            "message": "Temperature alert",
        },
    )


    assert event.event_type == "signal_received"


    assert event.source == "health"


    assert event.payload["severity"] == "critical"


    assert event.event_id is not None


    assert event.correlation_id is not None


    assert event.created_at is not None
