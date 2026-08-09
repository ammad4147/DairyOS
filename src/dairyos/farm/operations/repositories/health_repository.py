from abc import ABC, abstractmethod

from dairyos.farm.operations.models.health_observation import (
    HealthObservation,
)


class HealthRepository(ABC):
    """
    Repository boundary for health observations.
    """


    @abstractmethod
    def save(
        self,
        observation: HealthObservation,
    ):
        pass


    @abstractmethod
    def get_all(
        self,
    ) -> list[HealthObservation]:
        pass
