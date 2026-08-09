from dataclasses import dataclass, field
from datetime import datetime, timezone



@dataclass
class WorkflowDecision:
    """
    Operational decision generated from
    workflow rules and operational signals.

    This is rule-based intelligence.
    It does not perform autonomous decisions.
    """


    workflow_id: str


    decision_type: str


    severity: str


    recommended_action: str


    created_at: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )
