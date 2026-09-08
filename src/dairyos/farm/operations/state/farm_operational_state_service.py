from dairyos.farm.operations.alerts.operational_heads_up_service import (
    OperationalHeadsUpService,
)

from dairyos.farm.operations.state.operational_state_runtime import (
    OperationalStateRuntime,
)


from copy import deepcopy


class FarmOperationalStateService:
    """
    Application service for farm operational state.

    Canonical projection architecture:

        FarmOperationEvent
                |
                v
        FarmOperationEventBus
             /       \
            /         \
           v           v
    Farm state       Animal state
        |                 |
        v                 v
    OperationalState   AnimalEventProjection

    Animal operational state is NOT projected by this service.

    The event bus owns fan-out and each projection has one
    authoritative subscriber.
    """

    def __init__(
        self,
        repository=None,
        runtime=None,
        farm_id="TRIDENT-DAIRIES",
        animal_projection=None,
    ):
        self.heads_up_service = (
            OperationalHeadsUpService()
        )

        self.runtime = (
            runtime
            or OperationalStateRuntime(
                farm_id=farm_id,
                repository=repository,
            )
        )

        self.repository = repository

        # Retained for constructor compatibility with existing
        # composition wiring.
        #
        # IMPORTANT:
        # This reference is not invoked by this service.
        #
        # Animal state has one authoritative event-bus subscriber:
        #
        #     FarmOperationEventBus
        #             |
        #             v
        #     AnimalOperationalEventSubscriber
        #             |
        #             v
        #     AnimalEventProjection
        self.animal_projection = animal_projection

    def handle(
        self,
        event,
    ):
        """
        Handle a farm operational event.

        Animal projection is intentionally excluded.
        """

        return self.process_event(
            event
        )

    def handle_input(
        self,
        input_event,
    ):
        """
        Compatibility boundary for direct operational-input handling.

        New event-driven paths should publish through the canonical
        FarmOperationEventBus.
        """

        event = {
            "event_type": "operational_input_received",
            "input": input_event,
        }

        return self.process_event(
            event
        )

    def process_event(
        self,
        event,
    ):
        """
        Apply one event to current farm operational state.
        """

        state = self.runtime.ensure_state()

        event_id = getattr(event, "event_id", None)
        event_type = getattr(event, "event_type", None) or getattr(event, "name", "")
        identity = f"{event_id}:{event_type}" if event_id else None
        if identity and self.repository is not None:
            restored = self.repository.get_current(state.farm_id)
            if restored is not None and str(restored.operational_date) == str(state.operational_date):
                state = restored
                self.runtime.current_state = state
        applied = list(getattr(state, "applied_event_ids", []))
        if identity in applied:
            return state
        previous = deepcopy(state)

        state.record_event(
            event
        )

        notifications = (
            self.heads_up_service.evaluate(
                state
            )
        )

        state.heads_up_notifications = [
            {
                "notification_type":
                    notification.notification_type,

                "message":
                    notification.message,

                "severity":
                    notification.severity,
            }
            for notification in notifications
        ]

        if identity:
            state.applied_event_ids = [*applied, identity]
        try:
            self.runtime.persist_state()
        except Exception:
            self.runtime.current_state = previous
            raise

        return state

    def get_state(
        self,
    ):
        return self.runtime.get_state()
