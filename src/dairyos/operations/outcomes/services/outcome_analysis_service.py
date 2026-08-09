from typing import List

from ..models.operational_outcome import OperationalOutcome


class OutcomeAnalysisService:
    """
    Analyses completed operational outcomes.
    """

    def successful_outcomes(
        self,
        outcomes: List[OperationalOutcome],
    ) -> List[OperationalOutcome]:

        return [
            outcome
            for outcome in outcomes
            if outcome.rating.rating in [
                "GOOD",
                "EXCELLENT",
            ]
        ]


    def failed_outcomes(
        self,
        outcomes: List[OperationalOutcome],
    ) -> List[OperationalOutcome]:

        return [
            outcome
            for outcome in outcomes
            if outcome.rating.rating in [
                "POOR",
                "FAILED",
            ]
        ]

