from dataclasses import dataclass

from dairyos.operations.execution.models.operational_execution import (
    OperationalExecution,
)


@dataclass
class ExecutionRecord:
    """
    Legacy execution outcome / compatibility projection.

    ExecutionRecord is NOT an execution aggregate and does not own
    execution lifecycle state.

    The authoritative execution aggregate is:

        dairyos.operations.execution.models.OperationalExecution

    This DTO exists for legacy orchestration callers and integrations
    that require a compact historical/result representation.

    A record may retain a private reference to the canonical execution
    that produced it. That reference is informational only; lifecycle
    mutation must always occur through OperationalExecution and its
    ExecutionTrackingService.
    """

    action_type: str
    performed_by: str
    execution_status: str
    notes: str

    @property
    def canonical_execution(self) -> OperationalExecution | None:
        """
        Return the canonical execution represented by this projection.

        This does not make ExecutionRecord authoritative.
        """
        return getattr(self, "_canonical_execution", None)

    @classmethod
    def from_execution(
        cls,
        execution: OperationalExecution,
        performed_by: str,
        notes: str = "",
    ) -> "ExecutionRecord":
        """
        Build a legacy/result projection from canonical execution truth.

        The direction is deliberately one-way:

            OperationalExecution
                    |
                    v
            ExecutionRecord

        ExecutionRecord must never be used to create or mutate
        OperationalExecution state.
        """

        record = cls(
            action_type=execution.action_id,
            performed_by=performed_by,
            execution_status=execution.status.lower(),
            notes=notes,
        )

        record._canonical_execution = execution

        return record
