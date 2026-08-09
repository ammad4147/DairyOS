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
    """


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



    def create_execution(
        self,
        action_id: str,
        assigned_to: str,
    ) -> OperationalExecution:


        execution = OperationalExecution(

            execution_id=(
                f"EXE-{len(self.executions)+1:04d}"
            ),

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


        for execution in self.executions:

            if execution.execution_id == execution_id:

                return execution


        return None



    def list_executions(
        self,
    ) -> List[OperationalExecution]:

        return self.executions
