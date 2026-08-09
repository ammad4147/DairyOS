from typing import List

from ..models.operational_attention import OperationalAttention
from ..models.operational_command_status import OperationalCommandStatus


class OperationsCommandService:
    """
    Converts operational intelligence into command-center status.
    """

    def __init__(self):
        self.attentions: List[OperationalAttention] = []


    def register_attention(
        self,
        attention: OperationalAttention,
    ) -> OperationalAttention:

        self.attentions.append(attention)

        return attention


    def active_attentions(self) -> List[OperationalAttention]:

        return [
            attention
            for attention in self.attentions
            if not attention.resolved
        ]


    def generate_status(self) -> OperationalCommandStatus:

        active = self.active_attentions()

        if any(
            item.priority.upper() == "CRITICAL"
            for item in active
        ):
            health = "RED"
            focus = "Resolve critical operational issues"

        elif len(active) > 0:
            health = "AMBER"
            focus = "Review operational attention items"

        else:
            health = "GREEN"
            focus = "Maintain operational performance"


        return OperationalCommandStatus(
            health_status=health,
            active_attention_count=len(active),
            recommended_focus=focus,
            attentions=active,
        )
