from dairyos.intelligence.integration.autonomous_audit_bridge import (
    AutonomousAuditBridge,
)


def test_autonomous_audit_bridge_records_cycle():

    bridge = AutonomousAuditBridge()

    result = {
        "runtime": {
            "cycle_id": "cycle-001",
            "status": "completed",
            "stages": [
                "prediction",
            ],
            "stage_count": 1,
        },
        "runtime_validation": {
            "valid": True,
            "missing_fields": [],
        },
    }


    event = bridge.record_cycle(
        result
    )


    assert event.event_type == (
        "autonomous_cycle_completed"
    )

    assert event.source == (
        "autonomous_intelligence"
    )

    assert event.payload["cycle_id"] == (
        "cycle-001"
    )
