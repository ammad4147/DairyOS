class EffectivenessAnalysisService:
    """
    Provides effectiveness interpretation.
    """


    def evaluate(
        self,
        effectiveness,
    ):

        if effectiveness.overall_score >= 80:

            return "EFFECTIVE"


        if effectiveness.overall_score >= 50:

            return "PARTIALLY_EFFECTIVE"


        return "INEFFECTIVE"
