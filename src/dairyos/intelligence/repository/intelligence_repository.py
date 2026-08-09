from abc import ABC, abstractmethod

from dairyos.intelligence.kernel.models.intelligence_signal import (
    IntelligenceSignal,
)

from dairyos.intelligence.kernel.models.intelligence_decision import (
    IntelligenceDecision,
)

from dairyos.intelligence.kernel.models.intelligence_outcome import (
    IntelligenceOutcome,
)


class IntelligenceRepository(ABC):
    """
    Enterprise persistence contract for DairyOS intelligence data.

    This interface defines persistence operations
    without coupling the intelligence layer to
    any database technology.

    Future implementations may include:

    - PostgreSQL repository
    - SQLAlchemy adapter
    - Event store adapter
    - Cloud persistence adapter
    """


    @abstractmethod
    def save_signal(
        self,
        signal: IntelligenceSignal,
    ):
        pass


    @abstractmethod
    def save_decision(
        self,
        decision: IntelligenceDecision,
    ):
        pass


    @abstractmethod
    def save_outcome(
        self,
        outcome: IntelligenceOutcome,
    ):
        pass


    @abstractmethod
    def get_signals(
        self,
    ) -> list[IntelligenceSignal]:
        pass


    @abstractmethod
    def get_decisions(
        self,
    ) -> list[IntelligenceDecision]:
        pass


    @abstractmethod
    def get_outcomes(
        self,
    ) -> list[IntelligenceOutcome]:
        pass
