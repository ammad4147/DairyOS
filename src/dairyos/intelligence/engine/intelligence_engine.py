from dairyos.intelligence.models.intelligence_signal import (
    IntelligenceSignal,
)

from dairyos.intelligence.models.intelligence_recommendation import (
    IntelligenceRecommendation,
)


class IntelligenceEngine:
    """
    Central coordination layer for DairyOS intelligence.

    Collects signals and recommendations.
    Does not modify operational facts.
    """


    def __init__(self):

        self.signals = []

        self.recommendations = []



    def register_signal(
        self,
        signal: IntelligenceSignal,
    ):

        self.signals.append(
            signal
        )

        return signal



    def register_recommendation(
        self,
        recommendation: IntelligenceRecommendation,
    ):

        self.recommendations.append(
            recommendation
        )

        return recommendation



    def get_signals(
        self,
    ):

        return list(
            self.signals
        )



    def get_recommendations(
        self,
    ):

        return list(
            self.recommendations
        )



    def summary(
        self,
    ):

        return {

            "signal_count":
                len(self.signals),

            "recommendation_count":
                len(self.recommendations),

            "signals":
                self.signals,

            "recommendations":
                self.recommendations,

        }

