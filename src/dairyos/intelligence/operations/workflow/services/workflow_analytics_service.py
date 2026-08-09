class WorkflowAnalyticsService:
    """
    Analytics boundary for workflow intelligence.

    Calculates operational metrics from
    workflow intelligence projections.
    """


    def __init__(
        self,
        repository,
    ):

        self.repository = repository



    def total_workflows(
        self,
    ):

        return self.repository.count()



    def completed_workflows(
        self,
    ):

        return [

            workflow

            for workflow in self.repository.all()

            if workflow.status == "completed"

        ]



    def active_workflows(
        self,
    ):

        return [

            workflow

            for workflow in self.repository.all()

            if workflow.status != "completed"

        ]



    def completed_count(
        self,
    ):

        return len(
            self.completed_workflows()
        )



    def active_count(
        self,
    ):

        return len(
            self.active_workflows()
        )



    def average_completion_duration_seconds(
        self,
    ):

        durations = [

            workflow.duration_seconds()

            for workflow in self.completed_workflows()

            if workflow.duration_seconds() is not None

        ]


        if not durations:

            return 0


        return sum(durations) / len(durations)



    def workload_by_operator(
        self,
    ):

        workload = {}


        for workflow in self.repository.all():

            operator = workflow.assigned_to


            if operator not in workload:

                workload[operator] = 0


            workload[operator] += 1


        return workload
