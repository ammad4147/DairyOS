from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class FeedWorkflowEvent:
    """
    Workflow request generated from FeedOS intelligence.
    """

    domain: str
    animal_group: str
    issue_type: str
    severity: str
    priority: str
    recommended_action: str
    requires_action: bool
    message: str

    created_at: datetime = (
        datetime.now(UTC)
    )
