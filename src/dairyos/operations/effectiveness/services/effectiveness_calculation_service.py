class EffectivenessCalculationService:
    """
    Calculates operational effectiveness.
    """


    def calculate(
        self,
        response_score,
        resolution_score,
        closure_score,
    ):

        return (
            response_score
            + resolution_score
            + closure_score
        ) / 3
