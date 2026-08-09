from dataclasses import dataclass


@dataclass
class ActionAssignment:
    """
    Assigns operational responsibility.
    """

    assigned_to: str
    department: str

