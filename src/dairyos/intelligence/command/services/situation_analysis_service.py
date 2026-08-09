from dairyos.intelligence.command.models.farm_situation import (
    FarmSituation,
)


class SituationAnalysisService:
    """
    Creates farm operational situation assessments.
    """


    def __init__(
        self,
        repository,
    ):

        self.repository = repository


    def analyze(
        self,
        situation_id: str,
        farm_id: str,
        status: str,
        priority: str,
    ) -> FarmSituation:

        situation = FarmSituation(
            situation_id=situation_id,
            farm_id=farm_id,
            status=status,
            priority=priority,
        )

        return self.repository.save(
            situation
        )
