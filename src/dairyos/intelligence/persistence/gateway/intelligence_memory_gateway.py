from dairyos.intelligence.persistence.services.event_recorder import (
    EventRecorder,
)

from dairyos.intelligence.persistence.services.history.intelligence_history_service import (
    IntelligenceHistoryService,
)


class IntelligenceMemoryGateway:
    """
    Enterprise gateway for DairyOS intelligence memory.

    Provides unified access to:

    - event recording
    - intelligence history
    - decision timeline

    Keeps application services independent
    from persistence implementation.
    """


    def __init__(
        self,
        repository,
    ):

        self.recorder = EventRecorder(
            repository
        )

        self.history = IntelligenceHistoryService(
            repository
        )


    def record(
        self,
        event_type: str,
        source: str,
        payload: dict,
    ):

        return self.recorder.record(
            event_type=event_type,
            source=source,
            payload=payload,
        )


    def get_history(
        self,
    ):

        return self.history.get_history()


    def get_decision_timeline(
        self,
    ):

        return self.history.get_decision_timeline()
