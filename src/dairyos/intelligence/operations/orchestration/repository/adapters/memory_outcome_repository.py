from dairyos.intelligence.operations.orchestration.repository.outcome_repository import (
    OutcomeRepository,
)


class MemoryOutcomeRepository(OutcomeRepository):

    def __init__(self):
        self.outcomes = []


    def save(self, outcome):

        self.outcomes.append(outcome)

        return outcome


    def get_all(self):

        return self.outcomes
