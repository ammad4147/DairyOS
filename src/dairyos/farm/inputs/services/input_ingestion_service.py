from dairyos.domain.events.operational_input_received import (
    OperationalInputReceived,
)


class InputIngestionService:
    """
    Receives operational farm inputs,
    normalizes payloads,
    validates contracts,
    persists operational records,
    and publishes domain events.
    """

    def __init__(
        self,
        registry,
        event_publisher=None,
        tracking_service=None,
        governance_service=None,
        repository=None,
        normalization_service=None,
    ):

        self.registry = registry

        # Defensive fallback for event publisher to prevent TypeError on unsupplied callables
        self.event_publisher = (
            event_publisher
            if event_publisher is not None
            else lambda evt: None
        )

        self.tracking_service = (
            tracking_service
        )

        self.repository = (
            repository
        )

        self.governance_service = (
            governance_service
        )

        self.normalization_service = (
            normalization_service
        )


    def ingest(
        self,
        input_type: str,
        payload: dict,
        source: str,
        actor: str,
    ):

        if self.normalization_service:

            payload = (
                self.normalization_service.normalize(
                    input_type=input_type,
                    payload=payload,
                )
            )


        self.registry.validate(
            input_type,
            payload,
        )


        payload = {
            **payload,
            "input_type": input_type,
            "source": source,
            "actor": actor,
        }


        event = OperationalInputReceived(
            input_type=input_type,
            payload=payload,
            source=source,
            actor=actor,
        )

        propagation_id = payload.get("_propagation_id")
        if propagation_id:
            event.event_id = str(propagation_id)


        if self.repository:

            self.repository.save(
                event
            )


        # Most operational inputs preserve the historical defensive isolation.
        # Durable cross-store projections opt into strict publishing so a
        # PostgreSQL outbox can retain retry state instead of silently losing
        # a secondary projection failure.
        if payload.get("_require_durable_projection"):
            self.event_publisher(event)
        else:
            try:
                self.event_publisher(event)
            except Exception:
                pass


        if self.tracking_service:
            try:
                self.tracking_service.track(event)
            except Exception:
                pass


        if self.governance_service:
            try:
                self.governance_service.record(event)
            except Exception:
                pass


        return event
