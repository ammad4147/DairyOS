class InputLearningBridge:
    """
    Converts operational learning signals
    into intelligence indicators.
    """


    def __init__(
        self,
        pattern_service,
        deviation_service,
    ):

        self.pattern_service = (
            pattern_service
        )

        self.deviation_service = (
            deviation_service
        )



    def evaluate(
        self,
    ):

        patterns = (
            self.pattern_service
            .analyze()
        )


        return (
            self.deviation_service
            .detect(
                patterns
            )
        )
