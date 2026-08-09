class AlertResolutionService:
    """
    Handles operational alert closure.
    """


    def resolve(
        self,
        alert,
    ):

        alert.resolved = True

        return alert
