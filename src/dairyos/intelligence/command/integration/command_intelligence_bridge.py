class CommandIntelligenceBridge:
    """
    Connects command intelligence with
    existing intelligence layers.

    Future connections:

    - decision intelligence
    - workflow intelligence
    - execution intelligence
    - learning feedback
    """


    def __init__(
        self,
        command_gateway,
    ):

        self.command_gateway = command_gateway


    def get_gateway(
        self,
    ):

        return self.command_gateway
