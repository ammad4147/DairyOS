class DefaultCommandSetup:
    """
    Creates default command center providers.
    """



    def initialize(
        self,
        aggregator,
    ):


        aggregator.register_provider(

            "platform",

            aggregator,

        )


        return aggregator
