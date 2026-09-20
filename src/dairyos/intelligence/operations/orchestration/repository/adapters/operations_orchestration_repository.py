
from dairyos.intelligence.operations.orchestration.models.action_assignment import (
    ActionAssignment,
)
from dairyos.intelligence.operations.orchestration.models.action_outcome import (
    ActionOutcome,
)
from dairyos.intelligence.operations.orchestration.models.execution_record import (
    ExecutionRecord,
)
from dairyos.intelligence.operations.orchestration.models.operational_action import (
    OperationalAction,
)


class OperationsOrchestrationRepository:
    """
    In-memory repository for operational orchestration state.

    Provides deterministic storage abstraction
    before persistent database integration.

    Future extensions:

    - PostgreSQL persistence
    - event sourcing
    - operational history
    - audit tracking
    """


    def __init__(self):

        self.actions: list[OperationalAction] = []

        self.assignments: list[ActionAssignment] = []

        self.executions: list[ExecutionRecord] = []

        self.outcomes: list[ActionOutcome] = []


    def save_action(
        self,
        action: OperationalAction,
    ) -> OperationalAction:

        self.actions.append(action)

        return action



    def save_assignment(
        self,
        assignment: ActionAssignment,
    ) -> ActionAssignment:

        self.assignments.append(assignment)

        return assignment



    def save_execution(
        self,
        execution: ExecutionRecord,
    ) -> ExecutionRecord:

        self.executions.append(execution)

        return execution



    def save_outcome(
        self,
        outcome: ActionOutcome,
    ) -> ActionOutcome:

        self.outcomes.append(outcome)

        return outcome



    def get_actions(self) -> list[OperationalAction]:

        return self.actions



    def get_assignments(self) -> list[ActionAssignment]:

        return self.assignments



    def get_executions(self) -> list[ExecutionRecord]:

        return self.executions



    def get_outcomes(self) -> list[ActionOutcome]:

        return self.outcomes
