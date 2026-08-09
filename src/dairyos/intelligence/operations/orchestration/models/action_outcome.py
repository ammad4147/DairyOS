from dataclasses import dataclass


@dataclass
class ActionOutcome:
    """
    Represents the measured outcome
    of an operational action.

    Future extensions:

    - outcome scoring
    - learning feedback
    - effectiveness tracking
    """


    action_type: str

    result: str

    success: bool

    feedback: str
