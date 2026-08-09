from dairyos.intelligence.persistence.models.intelligence_event import (
    IntelligenceEvent,
)

from dairyos.intelligence.persistence.repositories.intelligence_event_repository import (
    IntelligenceEventRepository,
)


class MemoryEventRepository(
    IntelligenceEventRepository,
):
    """
    In-memory intelligence event repository.

    Provides deterministic storage for:

    - testing
    - development
    - future adapter validation
    """


    def __init__(
        self,
    ):

        self.events = []


    def save_event(
        self,
        event: IntelligenceEvent,
    ):

        self.events.append(
            event
        )

        return event


    def get_events(
        self,
    ) -> list[IntelligenceEvent]:

        return self.events


    def find_events_by_type(
        self,
        event_type: str,
    ) -> list[IntelligenceEvent]:

        return [
            event
            for event in self.events
            if event.event_type == event_type
        ]
