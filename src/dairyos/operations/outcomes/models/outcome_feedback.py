from dataclasses import dataclass


@dataclass
class OutcomeFeedback:
    """
    Learning feedback captured after execution.
    """

    what_worked: str
    what_failed: str
    improvement: str

