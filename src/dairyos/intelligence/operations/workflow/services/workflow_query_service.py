class WorkflowQueryService:
    """
    Query boundary for workflow intelligence.

    Provides read-only access to workflow
    intelligence projections.
    """


    def __init__(
        self,
        repository,
    ):

        self.repository = repository



    def get(
        self,
        workflow_id: str,
    ):

        return self.repository.get(
            workflow_id
        )



    def all(
        self,
    ):

        return self.repository.all()



    def count(
        self,
    ):

        return self.repository.count()



    def by_status(
        self,
        status: str,
    ):

        return [

            projection

            for projection in self.repository.all()

            if projection.status == status

        ]



    def active(
        self,
    ):

        return [

            projection

            for projection in self.repository.all()

            if projection.status != "completed"

        ]
