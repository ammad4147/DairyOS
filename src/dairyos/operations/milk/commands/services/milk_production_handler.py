class MilkProductionCommandHandler:
    """
    Converts milk commands into
    domain actions.
    """


    def __init__(
        self,
        service,
    ):

        self.service = service



    def handle(
        self,
        command,
    ):

        return self.service.record(
            command
        )
