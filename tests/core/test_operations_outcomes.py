from dairyos.operations.outcomes.services.outcome_record_service import (
    OutcomeRecordService,
)

from dairyos.operations.outcomes.services.feedback_service import (
    FeedbackService,
)


def test_record_operational_outcome():

    feedback = FeedbackService().create_feedback(
        worked="Backup supplier available",
        failed="Delay in notification",
        improvement="Create supplier register",
    )

    service = OutcomeRecordService()

    outcome = service.record_outcome(
        action_id="ACT-0001",
        result="Emergency feed arranged",
        rating="GOOD",
        feedback=feedback,
    )

    assert outcome.rating.rating == "GOOD"
    assert outcome.action_id == "ACT-0001"


def test_feedback_creation():

    feedback = FeedbackService().create_feedback(
        worked="Task completed",
        failed="None",
        improvement="Maintain process",
    )

    assert feedback.improvement == "Maintain process"

