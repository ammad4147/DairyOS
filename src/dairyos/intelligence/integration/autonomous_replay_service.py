"""
DairyOS Autonomous Replay Service

Provides deterministic replay inspection
for autonomous intelligence cycles.

Reads audit history without modifying
runtime execution.
"""


class AutonomousReplayService:
    """
    Reconstructs autonomous intelligence history.
    """


    def __init__(
        self,
        history_service=None,
    ):

        if history_service is None:

            from dairyos.intelligence.persistence.services.history.intelligence_history_service import (
                IntelligenceHistoryService,
            )

            from dairyos.intelligence.persistence.repositories.adapters.memory_event_repository import (
                MemoryEventRepository,
            )


            history_service = IntelligenceHistoryService(
                MemoryEventRepository()
            )


        self.history_service = history_service



    def get_autonomous_cycles(
        self,
    ):

        return (
            self.history_service
            .get_events_by_type(
                "autonomous_cycle_completed"
            )
        )



    def replay_cycle(
        self,
        cycle_id: str,
    ):

        events = self.get_autonomous_cycles()


        for event in events:

            if (
                event.payload.get(
                    "cycle_id"
                )
                == cycle_id
            ):

                return {
                    "cycle_id": cycle_id,
                    "event_id": event.event_id,
                    "created_at": event.created_at,
                    "status": event.payload.get(
                        "status"
                    ),
                    "stages": event.payload.get(
                        "stages",
                        [],
                    ),
                    "stage_count": event.payload.get(
                        "stage_count",
                        0,
                    ),
                }


        return None
