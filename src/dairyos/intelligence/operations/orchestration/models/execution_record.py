from dataclasses import dataclass


@dataclass
class ExecutionRecord:
    """
    Legacy execution outcome / compatibility projection.

    ExecutionRecord is intentionally NOT an execution aggregate.
    It has no lifecycle authority and must never be used as the source
    of truth for operational execution state.

    The authoritative source is:

        dairyos.operations.execution.models.OperationalExecution

    This DTO exists for existing orchestration callers and integrations
    that require a compact historical/result representation.
    """

    action_type: str
    performed_by: str
    execution_status: str
    notes: str
