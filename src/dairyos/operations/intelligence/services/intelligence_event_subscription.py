"""
Operational intelligence event subscription.

Connects EventBus events with
Operational Intelligence processing.
"""

from dairyos.operations.events.services.event_bus_service import (
    EventBusService,
)

from dairyos.operations.intelligence.services.operational_event_signal_service import (
    OperationalEventSignalService,
)


class IntelligenceEventSubscription:
    """
    Registers intelligence processing
    with the operational event bus.
    """


    def __init__(
        self,
        event_bus: EventBusService,
        signal_service: OperationalEventSignalService,
    ):

        self.event_bus = event_bus

        self.signal_service = signal_service



    def register(self):

        return self.event_bus.subscribe(
            self.signal_service.process_event
        )
