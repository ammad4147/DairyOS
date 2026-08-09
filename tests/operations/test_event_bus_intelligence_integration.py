from dairyos.operations.events.operational_event import (
    OperationalEvent,
)

from dairyos.operations.events.services.event_bus_service import (
    EventBusService,
)

from dairyos.operations.intelligence.services.operations_intelligence_service import (
    OperationsIntelligenceService,
)

from dairyos.operations.intelligence.services.operational_event_signal_service import (
    OperationalEventSignalService,
)

from dairyos.operations.intelligence.services.intelligence_event_subscription import (
    IntelligenceEventSubscription,
)



def test_event_bus_creates_intelligence_signal():

    event_bus = EventBusService()


    intelligence = (
        OperationsIntelligenceService()
    )


    signal_service = (
        OperationalEventSignalService(
            intelligence
        )
    )


    subscription = (
        IntelligenceEventSubscription(
            event_bus,
            signal_service,
        )
    )


    subscription.register()



    event = OperationalEvent(

        event_type="feeding",

        farm_id="trident",

        entity_id="cow101",

        performed_by="worker01",

    )


    event_bus.publish(
        event
    )


    signals = (
        intelligence.active_signals()
    )


    assert len(signals) == 1

    assert signals[0].category == "FEEDING"

    assert signals[0].source == (
        "OPERATIONAL_EVENT_ENGINE"
    )
