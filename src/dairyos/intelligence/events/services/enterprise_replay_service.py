"""
DairyOS Enterprise Replay Service

Provides deterministic replay inspection
using enterprise event history.
"""


class EnterpriseReplayService:
    """
    Reconstructs enterprise event timelines.
    """


    def __init__(
        self,
        query_service=None,
    ):

        if query_service is None:

            from dairyos.intelligence.events.services.event_query_service import (
                EventQueryService,
            )

            query_service = EventQueryService()


        self.query_service = query_service



    def replay_entity(
        self,
        entity_id: str,
    ):

        events = (
            self.query_service
            .get_event_history(
                entity_id
            )
        )


        return [
            {
                "event_id": event.event_id,

                "event_type": event.event_type,

                "source": event.source,

                "timestamp": event.created_at,

                "payload": event.payload,
            }

            for event in events
        ]
