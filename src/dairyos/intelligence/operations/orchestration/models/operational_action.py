from dataclasses import dataclass


@dataclass
class OperationalAction:
    """
    Represents the operational work that should happen.

    OperationalAction answers:

        "WHAT should happen?"

    It does not own execution progress. Actual execution state belongs to
    ``dairyos.operations.execution.models.OperationalExecution``.

    Future extensions belong here only when they describe the action
    itself, such as approval metadata, business rationale, or action
    history. Execution timestamps and execution lifecycle states do not.
    """

    action_type: str
    description: str
    priority: str
    status: str
    source_decision: str
