from dairyos.intelligence.kernel.models.intelligence_decision import (
    IntelligenceDecision,
)

from dairyos.intelligence.kernel.services.outcome_tracker import (
    OutcomeTracker,
)


def test_outcome_tracker_records_decision_result():

    tracker = OutcomeTracker()

    decision = IntelligenceDecision(
        action="Monitor situation",
        rationale="Health signal received",
    )

    outcome = tracker.record(decision)

    assert outcome.recommendation == "Monitor situation"
    assert outcome.status == "generated"
    assert tracker.count() == 1
