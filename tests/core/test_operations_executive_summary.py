from dairyos.operations.executive_summary.services.executive_summary_service import (
    ExecutiveSummaryService,
)

from dairyos.operations.executive_summary.services.executive_priority_service import (
    ExecutivePriorityService,
)

from dairyos.operations.executive_summary.models.executive_priority import (
    ExecutivePriority,
)



def test_executive_summary_critical():

    service = ExecutiveSummaryService()

    summary = service.generate(
        "EXEC-001",
        "RED",
        40,
    )

    assert summary.priority == ExecutivePriority.CRITICAL



def test_executive_priority_attention():

    service = ExecutiveSummaryService()

    summary = service.generate(
        "EXEC-002",
        "GREEN",
        90,
    )

    priority_service = ExecutivePriorityService()

    assert priority_service.requires_attention(summary) is False
