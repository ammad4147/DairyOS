from dataclasses import dataclass


@dataclass
class FeedWorkflowRequest:
    """
    Represents an operational action request generated from FeedOS intelligence.
    """

    animal_group: str
    issue_type: str
    severity: str
    recommended_action: str
    priority: str = "NORMAL"
