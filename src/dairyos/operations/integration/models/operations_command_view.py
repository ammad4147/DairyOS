from dataclasses import dataclass


@dataclass
class OperationsCommandView:
    """
    Unified operational command view.
    """

    operational_status: str
    priority_level: str
    active_actions: int
    performance_score: float
    management_attention_required: bool
    recommended_focus: str
