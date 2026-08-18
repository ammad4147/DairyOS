from typing import List, Optional

from ..models.operational_execution import (
    OperationalExecution,
)

from dairyos.runtime.persistent_event_journal import (
    PersistentEventJournal,
)

from ..events.execution_events import (
    ExecutionEvents,
)


class OperationalExecutionService:
    """
    Creates and manages farm operational executions.

    Execution creation is persisted through
    the operational event journal.

    Execution identifiers are globally unique within the
    application/database lifecycle and retain the established
    EXE-#### format.
    """

    _next_execution_number: int | None = None

    def __init__(
        self,
        event_journal: PersistentEventJournal | None = None,
    ):
        self.executions: List[OperationalExecution] = []

        self.event_journal = (
            event_journal
            if event_journal is not None
            else PersistentEventJournal()
        )

        self._ensure_execution_sequence()

    def _ensure_execution_sequence(
        self,
    ) -> None:
        """
        Initialize the process-wide execution sequence from
        persisted journal state.

        The sequence is shared by all OperationalExecutionService
        instances in the current process, while the journal provides
        recovery after process restart.
        """

        if (
            OperationalExecutionService._next_execution_number
            is None
        ):
            highest = self.event_journal.latest_execution_sequence()

            OperationalExecutionService._next_execution_number = (
                highest + 1
            )

    @classmethod
    def _allocate_execution_id(
        cls,
    ) -> str:
        """
        Allocate the next process-wide execution identifier.
        """

        if cls._next_execution_number is None:
            raise RuntimeError(
                "Execution sequence has not been initialized."
            )

        execution_number = (
            cls._next_execution_number
        )

        cls._next_execution_number += 1

        return f"EXE-{execution_number:04d}"

    def create_execution(
        self,
        action_id: str,
        assigned_to: str,
    ) -> OperationalExecution:
        """
        Create and persist one operational execution.
        """

        execution = OperationalExecution(
            execution_id=self._allocate_execution_id(),
            action_id=action_id,
            assigned_to=assigned_to,
        )

        self.executions.append(
            execution
        )

        self.event_journal.append(
            ExecutionEvents.created(
                execution
            )
        )

        return execution

    def get_execution(
        self,
        execution_id: str,
    ) -> Optional[OperationalExecution]:
        """
        Return an execution held by this service instance.
        """

        for execution in self.executions:
            if execution.execution_id == execution_id:
                return execution

        return None

    def list_executions(
        self,
    ) -> List[OperationalExecution]:
        """
        Return executions held by this service instance.
        """

        return self.executions
