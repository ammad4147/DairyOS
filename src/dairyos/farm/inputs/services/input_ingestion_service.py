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
        event_publisher,
        tracking_service=None,
        governance_service=None,
        repository=None,
        normalization_service=None,
    ):

        self.registry = registry

        self.event_publisher = (
            event_publisher
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


        if self.repository:

            self.repository.save(
                event
            )


        self.event_publisher(
            event
        )


        if self.tracking_service:

            self.tracking_service.track(
                event
            )


        if self.governance_service:

            self.governance_service.record(
                event
            )


        return event
