from dataclasses import dataclass, field


@dataclass
class ExecutiveOperationsSummary:
    health_status: str
    attention_count: int
    critical_issue_count: int
    owner_action_required: bool
    recommended_focus: str
    operational_priority_score: float
    critical_items: list[str] = field(default_factory=list)
