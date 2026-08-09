from dataclasses import dataclass


@dataclass
class OperationalAction:
    """
    Represents an operational action
    generated from intelligence decisions.

    Future extensions:

    - approval workflow
    - execution lifecycle
    - action history
    - autonomous scheduling
    """


    action_type: str

    description: str

    priority: str

    status: str

    source_decision: str
