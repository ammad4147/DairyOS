from dataclasses import dataclass


@dataclass
class OperationalHealthSnapshot:
    """
    Unified operational health view.
    """

    health_status: str
    operational_score: float
    active_decisions: int
    pending_actions: int
    tracked_outcomes: int
    learning_signals: int
    owner_attention_required: bool
