"""
DairyOS Enterprise Event Query Service

Read boundary for enterprise event history.

Responsibilities:

- query persisted intelligence events
- filter by event type
- expose lifecycle history
- keep consumers independent from repositories
"""


class EventQueryService:
    """
    Enterprise event history read service.
    """


    def __init__(
        self,
        repository=None,
    ):

        if repository is None:

            from dairyos.intelligence.persistence.repositories.adapters.memory_event_repository import (
                MemoryEventRepository,
            )

            repository = MemoryEventRepository()


        self.repository = repository



    def get_all_events(
        self,
    ):

        return self.repository.get_events()



    def get_events_by_type(
        self,
        event_type: str,
    ):

        return (
            self.repository.find_events_by_type(
                event_type
            )
        )



    def get_event_history(
        self,
        entity_id: str,
    ):

        events = self.get_all_events()


        return [
            event
            for event in events
            if event.payload.get(
                "entity_id"
            )
            == entity_id
        ]
