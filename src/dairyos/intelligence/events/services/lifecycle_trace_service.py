"""
DairyOS Lifecycle Trace Service

Provides high-level intelligence lifecycle
inspection.

Combines:

- correlation identity
- timeline events
- lifecycle summary
"""


class LifecycleTraceService:
    """
    Enterprise lifecycle trace boundary.
    """


    def __init__(
        self,
        timeline_service=None,
    ):

        if timeline_service is None:

            from dairyos.intelligence.events.services.event_timeline_service import (
                EventTimelineService,
            )

            timeline_service = EventTimelineService()


        self.timeline_service = timeline_service



    def trace(
        self,
        correlation_id: str,
    ):

        return (
            self.timeline_service
            .summarize_timeline(
                correlation_id
            )
        )
