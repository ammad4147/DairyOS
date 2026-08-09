from abc import ABC, abstractmethod


class SituationRepository(ABC):


    @abstractmethod
    def save(self, situation):
        pass
