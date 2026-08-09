class TaskHandler:
    """
    Base contract for operational task handlers.
    """

    def handle(
        self,
        task,
    ):

        raise NotImplementedError(
            "Task handlers must implement handle()"
        )
