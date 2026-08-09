from dataclasses import dataclass
from typing import List

from .control_attention import ControlAttention


@dataclass
class OperationsControlStatus:
    """
    Management control tower status.
    """

    control_status: str
    attention_required: bool
    priority_level: str
    focus_area: str
    attentions: List[ControlAttention]
