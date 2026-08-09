from dairyos.intelligence.persistence.repositories.intelligence_event_repository import (
    IntelligenceEventRepository,
)


class IntelligenceHistoryService:
    """
    Provides read access to intelligence history.

    Responsibilities:

    - retrieve recent intelligence events
    - search event history
    - expose operational timelines
    """


    def __init__(
        self,
        repository: IntelligenceEventRepository,
    ):

        self.repository = repository


    def get_history(
        self,
    ):

        return self.repository.get_events()


    def get_events_by_type(
        self,
        event_type: str,
    ):

        return (
            self.repository
            .find_events_by_type(
                event_type
            )
        )


    def get_decision_timeline(
        self,
    ):

        return (
            self.repository
            .find_events_by_type(
                "decision_created"
            )
        )
