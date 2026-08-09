from dataclasses import dataclass
from typing import List

from .operational_attention import OperationalAttention


@dataclass
class OperationalCommandStatus:
    """
    Management view of operational performance.
    """

    health_status: str
    active_attention_count: int
    recommended_focus: str
    attentions: List[OperationalAttention]

    @property
    def has_critical_attention(self) -> bool:
        return any(
            attention.priority.upper() == "CRITICAL"
            for attention in self.attentions
            if not attention.resolved
        )
