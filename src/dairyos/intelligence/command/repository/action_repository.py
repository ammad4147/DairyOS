from abc import ABC, abstractmethod


class ActionRepository(ABC):


    @abstractmethod
    def save(self, action):
        pass
