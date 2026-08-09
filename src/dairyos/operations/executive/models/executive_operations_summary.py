from dataclasses import dataclass, field
from typing import List


@dataclass
class ExecutiveOperationsSummary:
    health_status: str
    attention_count: int
    critical_issue_count: int
    owner_action_required: bool
    recommended_focus: str
    operational_priority_score: float
    critical_items: List[str] = field(default_factory=list)
