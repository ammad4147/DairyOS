from abc import ABC, abstractmethod

from dairyos.intelligence.decision.models.decision_recommendation import (
    DecisionRecommendation,
)


class DecisionRepository(ABC):
    """
    Enterprise persistence contract
    for decision intelligence data.

    Future implementations:

    - PostgreSQL repository
    - SQLAlchemy adapter
    - Event store adapter
    - Cloud persistence adapter
    """


    @abstractmethod
    def save(
        self,
        recommendation: DecisionRecommendation,
    ):
        pass


    @abstractmethod
    def get_all(
        self,
    ) -> list[DecisionRecommendation]:
        pass
