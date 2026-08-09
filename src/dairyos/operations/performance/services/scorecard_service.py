from typing import List

from ..models.performance_scorecard import PerformanceScorecard


class ScorecardService:
    """
    Creates operational scorecards.
    """

    def __init__(self):
        self.scorecards: List[PerformanceScorecard] = []


    def create_scorecard(
        self,
        scorecard: PerformanceScorecard,
    ) -> PerformanceScorecard:

        self.scorecards.append(scorecard)

        return scorecard


    def get_scorecards(self):

        return list(self.scorecards)
