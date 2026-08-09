from datetime import datetime

from ..models.executive_operations_summary import (
    ExecutiveOperationsSummary,
)

from ..models.executive_priority import (
    ExecutivePriority,
)


class ExecutiveSummaryService:
    """
    Creates executive operational summaries.
    """


    def generate(
        self,
        summary_id,
        operational_health,
        effectiveness_score,
    ):

        if operational_health == "RED":

            priority = ExecutivePriority.CRITICAL
            message = "Immediate operational attention required"

        elif effectiveness_score < 60:

            priority = ExecutivePriority.HIGH
            message = "Operational improvement required"

        elif effectiveness_score < 80:

            priority = ExecutivePriority.MEDIUM
            message = "Monitor operational performance"

        else:

            priority = ExecutivePriority.LOW
            message = "Operations performing effectively"


        return ExecutiveOperationsSummary(
            summary_id=summary_id,
            operational_health=operational_health,
            priority=priority,
            key_message=message,
            created_at=datetime.now(),
        )
