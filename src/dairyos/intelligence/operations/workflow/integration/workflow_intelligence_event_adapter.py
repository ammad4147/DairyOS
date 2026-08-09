from dairyos.platform.events.models.operational_event import (
    OperationalEvent,
)


class WorkflowIntelligenceEventAdapter:
    """
    Event integration boundary for workflow intelligence.

    Receives operational workflow events
    and forwards them into the intelligence
    projection layer.
    """


    def __init__(
        self,
        projection_service,
    ):

        self.projection_service = projection_service



    def handle(
        self,
        event: OperationalEvent,
    ):

        if event.entity_type != "workflow":

            return None


        return self.projection_service.process(
            event
        )
