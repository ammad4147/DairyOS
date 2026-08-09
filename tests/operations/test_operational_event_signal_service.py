from dairyos.operations.events.operational_event import (
    OperationalEvent,
)

from dairyos.operations.intelligence.services.operations_intelligence_service import (
    OperationsIntelligenceService,
)

from dairyos.operations.intelligence.services.operational_event_signal_service import (
    OperationalEventSignalService,
)


def test_operational_event_creates_signal():

    intelligence = (
        OperationsIntelligenceService()
    )

    bridge = (
        OperationalEventSignalService(
            intelligence
        )
    )


    event = OperationalEvent(
        event_type="milking",
        farm_id="trident",
        entity_id="cow102",
        performed_by="worker01",
    )


    signal = bridge.process_event(
        event
    )


    assert signal.category == "PRODUCTION"

    assert signal.severity == "LOW"

    assert len(
        intelligence.active_signals()
    ) == 1
