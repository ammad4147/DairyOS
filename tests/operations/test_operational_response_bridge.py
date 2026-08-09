from datetime import datetime, timezone

from dairyos.operations.intelligence.models.operational_signal import (
    OperationalSignal,
)

from dairyos.operations.intelligence.services.operational_response_bridge import (
    OperationalResponseBridge,
)


def test_operational_signal_response_pipeline():


    bridge = OperationalResponseBridge()


    signal = OperationalSignal(

        signal_id="SIG-001",

        category="MILKING_DELAY",

        description="Morning milking delayed",

        severity="HIGH",

        source="Farm Operations",

        created_at=datetime.now(
            timezone.utc
        ),

    )


    response = bridge.process_signal(
        signal,
        delay_hours=10,
    )


    assert (
        response["decision"]
        .priority.level
        == "HIGH"
    )


    assert (
        response["alert"]
        .severity.value
        == "WARNING"
    )


    assert (
        response["escalation"]
        .level.value
        == "LEVEL_TWO"
    )


    assert (
        response["escalation"]
        .assigned_to
        == "Farm Manager"
    )
