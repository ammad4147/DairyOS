"""
DairyOS Event Timeline Service

Builds chronological lifecycle views
from enterprise intelligence events.

Responsibilities:

- group events by correlation identity
- order lifecycle events
- expose trace timelines

Does not modify persistence.
"""


class EventTimelineService:
    """
    Enterprise event lifecycle timeline reader.
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



    def get_timeline(
        self,
        correlation_id: str,
    ):

        events = (
            self.query_service
            .get_all_events()
        )


        timeline = [
            event
            for event in events
            if event.correlation_id
            == correlation_id
        ]


        return sorted(
            timeline,
            key=lambda event: event.created_at,
        )



    def summarize_timeline(
        self,
        correlation_id: str,
    ):

        events = self.get_timeline(
            correlation_id
        )


        return {
            "correlation_id": correlation_id,

            "event_count": len(events),

            "events": [
                {
                    "event_id": event.event_id,

                    "event_type": event.event_type,

                    "source": event.source,

                    "timestamp": event.created_at,

                }

                for event in events
            ],
        }
