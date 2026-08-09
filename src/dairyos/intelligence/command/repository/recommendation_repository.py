from abc import ABC, abstractmethod


class RecommendationRepository(ABC):


    @abstractmethod
    def save(self, recommendation):
        pass
