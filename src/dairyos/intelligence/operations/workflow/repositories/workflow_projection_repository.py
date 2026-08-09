from dairyos.intelligence.operations.workflow.models.workflow_projection import (
    WorkflowProjection,
)


class WorkflowProjectionRepository:
    """
    In-memory intelligence projection repository.

    Stores workflow read models generated
    from operational events.
    """


    def __init__(
        self,
    ):

        self._projections = {}



    def save(
        self,
        projection: WorkflowProjection,
    ):

        self._projections[
            projection.workflow_id
        ] = projection


        return projection



    def get(
        self,
        workflow_id: str,
    ):

        return self._projections.get(
            workflow_id
        )



    def all(
        self,
    ):

        return list(
            self._projections.values()
        )



    def count(
        self,
    ):

        return len(
            self._projections
        )
