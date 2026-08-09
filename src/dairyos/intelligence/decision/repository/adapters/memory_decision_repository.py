from dairyos.intelligence.decision.repository.decision_repository import (
    DecisionRepository,
)


class MemoryDecisionRepository(
    DecisionRepository
):
    """
    In-memory decision repository.

    Used for:

    - testing
    - development
    - deterministic validation

    Future replacement:

    PostgreSQL implementation.
    """


    def __init__(
        self,
    ):

        self.decisions = []


    def save(
        self,
        recommendation,
    ):

        self.decisions.append(
            recommendation
        )


    def get_all(
        self,
    ):

        return self.decisions
