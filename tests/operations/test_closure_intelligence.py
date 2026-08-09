from dairyos.operations.closure_intelligence.services.closure_intelligence_service import (
    ClosureIntelligenceService,
)


def test_successful_execution_closure():

    service = ClosureIntelligenceService()

    assessment = service.assess(
        execution_id="EXE-0001",
        task_name="Morning Milking",
        completed=True,
        performance_score=100.0,
    )

    assert assessment.execution_id == "EXE-0001"

    assert assessment.task_name == "Morning Milking"

    assert assessment.completed is True

    assert assessment.performance_score == 100.0

    assert assessment.closure_status == "SUCCESS"


def test_incomplete_execution_requires_followup():

    service = ClosureIntelligenceService()

    assessment = service.assess(
        execution_id="EXE-0002",
        task_name="Feed Preparation",
        completed=False,
        performance_score=0.0,
    )

    assert assessment.closure_status == "OPEN"

    assert (
        "Follow up"
        in assessment.recommendation
    )
