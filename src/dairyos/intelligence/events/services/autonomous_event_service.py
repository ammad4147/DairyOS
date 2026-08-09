from dairyos.intelligence.events.services.enterprise_event_service import (
    EnterpriseEventService,
)


class AutonomousEventService:
    """
    Creates standardized autonomous intelligence events.
    """

    def __init__(
        self,
        event_service=None,
    ):

        self.event_service = (
            event_service
            if event_service
            else EnterpriseEventService()
        )


    def cycle_completed(
        self,
        runtime,
        validation=None,
    ):

        return self.event_service.create_event(

            event_type="autonomous_cycle_completed",

            source="autonomous_intelligence",

            actor="system",

            entity_type="autonomous_cycle",

            entity_id=runtime.get(
                "cycle_id"
            ),

            payload={
                "status": runtime.get(
                    "status"
                ),

                "stages": runtime.get(
                    "stages",
                    [],
                ),

                "stage_count": runtime.get(
                    "stage_count",
                    0,
                ),

                "runtime_validation": validation,
            },
        )
