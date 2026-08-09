from dairyos.intelligence.persistence.models.intelligence_event import (
    IntelligenceEvent,
)

from dairyos.intelligence.persistence.repositories.intelligence_event_repository import (
    IntelligenceEventRepository,
)


class EventRecorder:
    """
    Records intelligence activities into
    persistent event history.

    Keeps intelligence processing separate
    from persistence implementation.
    """


    def __init__(
        self,
        repository: IntelligenceEventRepository,
    ):

        self.repository = repository


    def record(
        self,
        event_type: str,
        source: str,
        payload: dict,
    ) -> IntelligenceEvent:

        event = IntelligenceEvent(
            event_type=event_type,
            source=source,
            payload=payload,
        )


        return self.repository.save_event(
            event
        )
