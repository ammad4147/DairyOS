from abc import ABC, abstractmethod

from ..models.event import PlatformEvent


class EventHandler(ABC):
    """
    Enterprise event processing contract.
    """

    @abstractmethod
    def handle(self, event: PlatformEvent) -> None:
        """
        Process a platform event.
        """
        pass
