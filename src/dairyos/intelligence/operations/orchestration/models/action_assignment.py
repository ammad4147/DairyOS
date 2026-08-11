from dataclasses import dataclass


@dataclass
class ActionAssignment:
    """
    Represents ownership of an operational action.

    Assignment answers:

        "WHO should do it?"

    Assignment does not own completion or execution progress. Once an
    assigned action is dispatched, the canonical OperationalExecution
    aggregate owns the execution lifecycle.
    """

    action_type: str
    assigned_to: str
    assigned_role: str
    status: str
