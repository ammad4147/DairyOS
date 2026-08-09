class CommandHandler:
    """
    Base operational command handler.
    """

    def handle(
        self,
        command,
    ):

        raise NotImplementedError(
            "Command handler must implement handle()"
        )
