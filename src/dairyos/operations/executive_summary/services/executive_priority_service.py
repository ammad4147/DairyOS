from ..models.executive_priority import ExecutivePriority


class ExecutivePriorityService:
    """
    Determines management urgency.
    """


    def requires_attention(
        self,
        summary,
    ):

        return summary.priority in [
            ExecutivePriority.HIGH,
            ExecutivePriority.CRITICAL,
        ]
