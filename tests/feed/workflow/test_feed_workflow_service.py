from dairyos.feed.workflow import (
    FeedWorkflowService,
)

from dairyos.feed.intelligence.models import (
    FeedSignal,
    FeedSignalType,
    FeedSignalSeverity,
)


def create_high_variance_signal():

    return FeedSignal(
        signal_type=FeedSignalType.INTAKE_VARIANCE,
        severity=FeedSignalSeverity.HIGH,
        animal_group="MILKING_COWS",
        expected_intake=25,
        actual_intake=20,
        variance_percentage=-20,
        message="Feed intake variance -20%",
    )


def create_medium_variance_signal():

    return FeedSignal(
        signal_type=FeedSignalType.INTAKE_VARIANCE,
        severity=FeedSignalSeverity.MEDIUM,
        animal_group="DRY_COWS",
        expected_intake=18,
        actual_intake=16,
        variance_percentage=-11,
        message="Feed intake variance -11%",
    )


def test_high_feed_signal_creates_urgent_workflow():

    service = FeedWorkflowService()

    request = service.create_workflow_request(
        create_high_variance_signal()
    )

    assert request.animal_group == "MILKING_COWS"
    assert request.issue_type == "INTAKE_VARIANCE"
    assert request.severity == "HIGH"
    assert request.priority == "URGENT"


def test_medium_feed_signal_creates_high_priority_workflow():

    service = FeedWorkflowService()

    request = service.create_workflow_request(
        create_medium_variance_signal()
    )

    assert request.priority == "HIGH"


def test_workflow_contains_action():

    service = FeedWorkflowService()

    request = service.create_workflow_request(
        create_high_variance_signal()
    )

    assert (
        "Investigate feed delivery"
        in request.recommended_action
    )
