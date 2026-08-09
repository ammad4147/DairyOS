from abc import ABC, abstractmethod

from dairyos.intelligence.persistence.models.intelligence_event import (
    IntelligenceEvent,
)


class IntelligenceEventRepository(ABC):
    """
    Persistence contract for intelligence event history.

    Defines storage operations without coupling
    DairyOS intelligence to any persistence technology.

    Future implementations:

    - PostgreSQL adapter
    - SQLAlchemy repository
    - Event store adapter
    - Cloud persistence adapter
    """


    @abstractmethod
    def save_event(
        self,
        event: IntelligenceEvent,
    ):
        pass


    @abstractmethod
    def get_events(
        self,
    ) -> list[IntelligenceEvent]:
        pass


    @abstractmethod
    def find_events_by_type(
        self,
        event_type: str,
    ) -> list[IntelligenceEvent]:
        pass
