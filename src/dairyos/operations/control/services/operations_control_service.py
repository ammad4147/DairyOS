from typing import List

from ..models.control_attention import ControlAttention
from ..models.operations_control_status import OperationsControlStatus


class OperationsControlService:
    """
    Converts operational health conditions into management priorities.
    """


    def __init__(self):
        self.attentions: List[ControlAttention] = []


    def register_attention(
        self,
        attention: ControlAttention,
    ) -> ControlAttention:

        self.attentions.append(attention)

        return attention


    def generate_status(self) -> OperationsControlStatus:

        if any(
            item.severity.upper() == "CRITICAL"
            for item in self.attentions
        ):
            return OperationsControlStatus(
                control_status="RED",
                attention_required=True,
                priority_level="CRITICAL",
                focus_area="Resolve critical operational issues",
                attentions=self.attentions,
            )


        if len(self.attentions) > 0:
            return OperationsControlStatus(
                control_status="AMBER",
                attention_required=True,
                priority_level="HIGH",
                focus_area="Review operational exceptions",
                attentions=self.attentions,
            )


        return OperationsControlStatus(
            control_status="GREEN",
            attention_required=False,
            priority_level="NORMAL",
            focus_area="Maintain operational performance",
            attentions=[],
        )
