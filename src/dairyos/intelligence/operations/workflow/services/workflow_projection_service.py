from dairyos.platform.events.models.operational_event import (
    OperationalEvent,
)


from dairyos.intelligence.operations.workflow.models.workflow_projection import (
    WorkflowProjection,
)


class WorkflowProjectionService:
    """
    Builds workflow intelligence projections
    from operational events.
    """


    def __init__(
        self,
        repository,
    ):

        self.repository = repository



    def process(
        self,
        event: OperationalEvent,
    ):

        if event.event_type == "workflow_created":

            return self._handle_created(
                event
            )


        if event.event_type == "workflow_started":

            return self._handle_started(
                event
            )


        if event.event_type == "workflow_completed":

            return self._handle_completed(
                event
            )


        return None



    def _handle_created(
        self,
        event,
    ):

        projection = WorkflowProjection(

            workflow_id=event.entity_id,

            workflow_type=event.payload[
                "workflow_type"
            ],

            assigned_to=event.actor,

            status=event.payload[
                "status"
            ],

        )


        return self.repository.save(
            projection
        )



    def _handle_started(
        self,
        event,
    ):

        projection = self.repository.get(
            event.entity_id
        )


        if projection is None:
            return None


        projection.status = event.payload[
            "status"
        ]

        projection.started_at = event.timestamp


        return self.repository.save(
            projection
        )



    def _handle_completed(
        self,
        event,
    ):

        projection = self.repository.get(
            event.entity_id
        )


        if projection is None:
            return None


        projection.status = event.payload[
            "status"
        ]

        projection.completed_at = event.timestamp


        return self.repository.save(
            projection
        )
