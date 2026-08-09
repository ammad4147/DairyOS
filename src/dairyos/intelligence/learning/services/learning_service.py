from dairyos.intelligence.learning.services.pattern_analyzer import (
    PatternAnalyzer,
)

from dairyos.intelligence.learning.repository.learning_repository import (
    LearningRepository,
)


class LearningService:
    """
    Enterprise intelligence learning service.

    Coordinates:

    - pattern analysis
    - learning signal creation
    - learning persistence
    """


    def __init__(
        self,
        repository: LearningRepository,
    ):

        self.repository = repository

        self.analyzer = PatternAnalyzer()


    def learn(
        self,
        events: list,
    ):

        signals = self.analyzer.analyze(
            events
        )


        for signal in signals:

            self.repository.save(
                signal
            )


        return signals


    def get_learning_signals(
        self,
    ):

        return self.repository.get_all()
