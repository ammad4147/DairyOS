from dairyos.farm.operations.models.farm_operation_event import (
    FarmOperationEvent,
)


class OperationalStateEventSubscriber:
    """
    Sole event-bus subscriber responsible for projecting
    FarmOperationEvent instances into farm operational state.

    Ownership:

        FarmOperationEventBus
                |
                v
        OperationalStateEventSubscriber
                |
                v
        FarmOperationalStateService
    """

    def __init__(self, operational_state_service):
        self.operational_state_service = (
            operational_state_service
        )

    def handle(self, event: FarmOperationEvent):
        """
        Apply one operational event to farm state.
        """

        return self.operational_state_service.process_event(
            event
        )
