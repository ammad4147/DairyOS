from dataclasses import dataclass


@dataclass
class OperationalGap:
    """
    Represents an operational expectation
    that has not been fulfilled.

    Composition model only.
    No business rules.
    """

    area: str

    expected_activity: str

    message: str

    severity: str

    action_required: bool = True
