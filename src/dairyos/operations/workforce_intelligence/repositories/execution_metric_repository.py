class ExecutionMetricRepository:
    """
    Stores workforce execution metrics.
    """


    def __init__(
        self,
    ):

        self._metrics = {}



    def save(
        self,
        metric,
    ):

        self._metrics[
            metric.metric_id
        ] = metric


        return metric



    def get(
        self,
        metric_id,
    ):

        return self._metrics.get(
            metric_id
        )



    def all(
        self,
    ):

        return list(
            self._metrics.values()
        )



    def by_user(
        self,
        user_id,
    ):

        return [

            metric

            for metric in self._metrics.values()

            if metric.user_id == user_id

        ]



    def count(
        self,
    ):

        return len(
            self._metrics
        )
